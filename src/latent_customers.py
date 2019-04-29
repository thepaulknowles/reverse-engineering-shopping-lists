import pandas as pd
import numpy as np
from scipy import sparse
from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
#%matplotlib inline
import rainbow
import os
import glob
import time
from sklearn.decomposition import NMF
from sklearn import decomposition, datasets, model_selection, preprocessing, metrics

def json_to_df(path):
    all_files = glob.glob(os.path.join(path, "*.json"))
    df = pd.concat((pd.read_json(f,keep_default_dates=False,lines=True) for f in all_files)) 
    df=df[df['type']=='Checkout']
    df.drop(columns='type',inplace=True)
    df=df[df['term']<10]
    df['date']=pd.to_datetime(df['date'],yearfirst=True)
    df['day_of_week']=df['date'].dt.day_name()
    df['month']=df['date'].dt.month
    df['hour']=pd.to_datetime(df['time']).dt.hour
    
    
    return df


def get_items(df,most_common=10,least_common=5):
    
    stoppers = ['BAG CREDIT','SF Bag Charge','Gift Card Reload','8 OZ BIO TUB t3', '16OZ BIO TUB t4',
                 '32OZ BIO TUB t5','8 OZ PLSTC TUB t3','16 OZ PLSTC TUB t4','BOTTLE DEPOSIT','6PACK BEER SMALL C','PAID IN','Gift Card Sale',
                'PACKAGED FOOD', ]  
    '''build a dictionary where the keys are the words
    in the dataframe items column'''
    stopwords =[]
    items=[]
    item_dict = defaultdict(int)
    basket_counts=[]
    
    for basket in df['items']:
        basket_counts.append(len(basket))
        for item in basket:
            if item[0]=='MP':
                pass
            items.append(item[1])
            item_dict[item[1]] += 1
    
    items_set=set(items)

    '''add the most common words to the stopwords list'''
    stopwords=list([i[0] for i in Counter(item_dict).most_common(most_common)])
            
    '''add predetermined stoppers to stopwords list'''
    for s in stoppers:
        stopwords.append(s)
        
    '''add items containing "CRV" to the stopwords list'''
    for item in items_set:
        if "crv" in item.lower():
            stopwords.append(item)
    
    '''add the least common words to the stopwords list'''
    for key,value in item_dict.items():
        if value < least_common:
            stopwords.append(key)
    stopwords_set = set(stopwords)
    
    '''iterate through the baskets and add items to items_set
    if not in stopwords (too common or too uncommon)'''
    for stops in stopwords_set:
        if stops in items_set:
            items_set.remove(stops)
  

    return items_set,stopwords_set, item_dict, basket_counts

def build_matrix(df,items_set,stopwords,dept_to_exclude=()):

    
    item_matrix = np.zeros((df.shape[0],len(items_set)))
    df_items = pd.DataFrame(item_matrix,columns=items_set)
    df = df.reset_index()
    df.pop('index')
    col_index_dict = dict(zip(items_set, range(len(items_set))))
    
    matrix_dict = defaultdict(int)
    for i in range(df.shape[0]):
        for item in df['items'][i]:
            #set matrix to boolean for item precence in basket:
            if item[1] not in stopwords and item[3] not in dept_to_exclude:
                if item[2] > 0:
                    value = 1
                elif item[2] == 0:
                    value = 0
                else:
                    value = -1
                matrix_dict[i,col_index_dict[item[1]]] += value
    #convert matrix to sparse matrix
    rows, cols, vals = [], [], []
    for key, value in matrix_dict.items():
        rows.append(key[0])
        cols.append(key[1])
        vals.append(matrix_dict[key])
    sparse_matrix = sparse.csr_matrix((vals, (rows, cols)))
    #change negative values in matrix to 0
    sparse_matrix = (sparse_matrix > 0).astype(int)
    sum_of_zeros=sum(np.sum(sparse_matrix,axis=1)==0)
    print(sum_of_zeros / sparse_matrix.shape[0],"% of zero weight baskets")
    return sparse_matrix


def fit_NMF(sparse_matrix_,n_components_,max_iter=250):
    from sklearn.decomposition import NMF
    model = NMF(n_components=n_components_,max_iter=max_iter)
    W = model.fit_transform(sparse_matrix_)
    H=model.components_
    model_iter = model.n_iter_
    
    print('iterations:',model_iter,'W shape:',W.shape,'H shape:',H.shape)
    w = np.zeros_like(W)
    
    w[np.arange(len(W)), W.argmax(1)] = 1
    topic_strength = np.sum(w,axis=0)
    topic_strength = np.round(topic_strength/topic_strength.sum(),2)
    for i,t in enumerate(topic_strength):
        print('topic %d strength: %f '%(i,t))
    
    return model,W,H,model_iter,topic_strength

def print_top_items(model, feature_names, n_top_words):
    topic_dict = defaultdict()
    topics_list =[]
    fig = plt.figure(1,figsize=(100,100))
    for topic_idx, topic in enumerate(model.components_):
        print(topic_strength[topic_idx],"Topic #%d of %d:" %( topic_idx,number_of_components))
        #topic_string=(" ".join([feature_names[i]for i in topic.argsort()[:-n_top_words - 1:-1]]))
        topic_string=[feature_names[i]for i in topic.argsort()[:-n_top_words - 1:-1]]
        topic_dict[topic_idx]=topic_string
        topics_list.append(topic_string)
        print(topic_string)
        #print()
        wordcloud = WordCloud(max_font_size=500, max_words=1000, background_color="white").generate(str(topic_string).replace(" ", '').replace("'",""))
        #wordcloud = WordCloud(max_font_size=500, max_words=1000, background_color="white").generate(str(topic_string).replace("'","").replace(",",""))
        ax = fig.add_subplot(1,number_of_components,topic_idx+1)
        ax.imshow(wordcloud)
        ax.axis("off")
        # Display the generated image:
        #plt.figure(1,figsize=(10,10))
        '''plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()'''
        #plt.savefig('topic%d.png'%topic_idx)
        #plt.close()
        img_time=str(time.time()).split('.')[0]
        wordcloud.to_file('./img/2018/%s.topic%d.png'%(img_time,topic_idx))
        print('<img src="./img/2018/%s.topic%d.png">'%(img_time,topic_idx))

    topic_compare = np.zeros([len(topic_dict),len(topic_dict)])

    for topic in topic_dict:
        for item in topic_dict[topic]:
            for topic2 in topic_dict:
                if item in topic_dict[topic2]:
                    topic_compare[topic,topic2]+=1
    print ('topic similarity matix:')
    print (topic_strength)            
    print(topic_compare)

    topic_matrix=np.array(topics_list).T
    topic_matrix.shape

    topic_matrix=np.array(topics_list).T
    print (topic_matrix.shape)
    topic_df = pd.DataFrame(topic_matrix,columns=topic_strength)
    import tabulate 
    print(tabulate.tabulate(topic_df.values,topic_df.columns, tablefmt="pipe")) 
    return topic_dict,topics_list
    

if __name__ == '__main__':

    number_of_components = int(input('How many topics would you like to decompose into?'))
    print("Building Dataframe")
    df = json_to_df(input('path to jsons'))

    print('Building item set and stopwords')
    items_set,stopwords_set, item_dict, basket_counts = get_items(df,most_common=5,least_common=30)
    input("item set is ready, proceed?")
    print('Building sparse matrix')
    sparse_matrix = build_matrix(df,items_set,stopwords_set)
    input("matrix ready, proceed?")
    print('fitting model')
    model,W,H,model_iter,topic_strength = fit_NMF(sparse_matrix,n_components_=number_of_components,max_iter=250)
    input("model is ready, proceed?")
    n_top_words=int(input('How many top words would you like to see?'))
    topic_dict,topics_list = print_top_items(model,list(items_set),n_top_words)

