# Reverse Engineering Shopping Lists 
# The Problem: How can a grocery store analyze their customer's shopping without a loyalty program?

A large Bay-Area Natural Food store doesn’t have a method to analyze their customer's baskets.
They have been a fixture of San Francisco since 1975 and have a register system designed in the 80's.

* $1,000,000 in sale per week
* 25,000 square foot
* maintains a selection of 30,000 items
* 2000-3000 customer per day
* no loyalty program 

<p align="middle">
<img src = "./img/store/spices.jpg" width="200" />
<img src = "./img/store/bulk.jpg" width="200" />
<img src = "./img/store/produce1.jpg" width="200" />
<img src = "./img/store/vits.jpg" width="200" />
</p>

## Discovering customer types from transactions without a loyalty program!


Everyday the register spits out a giant raw text file (2000 printable pages) of the previous day's 2000-3000 transactions.
<p align="middle">
<img src = "./img/store/TLOG1.png" width="250" />
<img src = "./img/store/TLOG2.png" width="250" />
<img src = "./img/store/TLOG3.png" width="250" />
</p>

Is there a way to find some patterns of shopping in this run-on stream of text?

## Hello Non-Negative Matrix Factorization!

[NMF](https://en.wikipedia.org/wiki/Non-negative_matrix_factorization) is an unsupervised learning model that can be used to find topic similiarity between documents based on the words they contain. Treating each transaction as a document and each item's **unique 13 character description** as a word I will discover the latent dimensions of shopping baskets hidden in this history of purchases.
 
## Step 1. Parse the Data

Using a regex file I found on the web, i modified it to parse the transactionlog.txt ('tlogs') into useable elements. Date, time, total, cashier, lane, items, price and department code were all waiting to be pulled from a consistently formated text file.  I also had to account for stray punctuation characters in the item descriptions.
Writing the results into a json format allowed for them to be quickly read into a pandas dataframe.

## Step 2. Prepare the Item List and Dictionary

The item data was extracted as a list of list which I iterated through, adding the item to a dictionary with a running count of the items, ultimately yielding a dictionary of all the items in the all the baskets, and their total count.  I developed a "stop words" list to remove common items which made basket similarites worse. Bag Credits and bottle deposits were linking too many baskets because they were present in many baskets but were not actual items that lend any insight into shopping habits.  
Bananas were in 112832 of the 831284 baskets, roughly 1 in 8 baskets, or 13.5% of transactions and Hass Avocados were in 10% of baskets.
Removing both of these items allowed a greater differentiation between baskets.

## Step 3. Builing a Sparse Matrix

Because I needed the items descriptions to remain entact at the entire 13-character string, I built my own vectorizer. Each time an iten was present in the basket, I added 1. If the value was negative (such as a voided item) I subtracted 1. Iterating through the lists of transactions and adding a dicitonary key for the row (transaction) and a tuple of the item and its count in the basket I built up a dictionary object which was then passed to a sparse matrix.

## Step 4. Pass the Matrix to the NMF Model

Just before passing the sparse matrix to the NMF model, I set any negative values to 0. After choosing a value for the number of components (topics) and maximum iterations I let the NMF work its magic.  I returned from the model the number of iterations the model used to achieve the number of components specified, the matrix W and H


