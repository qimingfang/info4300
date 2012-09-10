# Assignment 1
# INFO 4300 Fall 2012
# Qiming Fang (qf26)
#
# This project was developed using python 2.7.2 on MacOSX 10.8.1
#
# To run with normal BST: python main.py -d data -s stoplist.txt
# To run with AVL tree: python main.py -d data -s stoplist.txt -a
#

from optparse import OptionParser
import sys
import glob
import os
import math

# How many relevant words do we want to cache per indexed term
REL_WORDS = 10

# Do we want to use AVL trees?
use_avl_tree = False

# Total number of docs
total_docs = 0

# Words we consider in the stop list
stop_list = []

# An instance of TreeNode is a node in the binary search tree that holds a pointer
# to its left chid, right child, and a Postings data.
class TreeNode:
    def __init__(self, d):
        self.left = None
        self.right = None
        self.data = d

    # The following four rotate methods are found on prof Graeme Bailey's lectures
    # http://www.cs.cornell.edu/courses/cs2110/2010sp/
    #
    # Inspiration was also obtained from an online blog:
    # http://bjourne.blogspot.com/2006/11/avl-tree-in-python.html
    
    def rotate_left(self):
        self.data, self.right.data = self.right.data, self.data
        old_left = self.left

        self.left, self.right = self.right, self.right.right
        self.left.right, self.left.left = self.left.left, old_left

    def rotate_right(self):
        self.data, self.left.data = self.left.data, self.data
        old_right = self.right

        self.left, self.right = self.left.left, self.left
        self.right.left, self.right.right = self.right.right, old_right

    def rotate_left_right(self):
        self.left.rotate_left()
        self.rotate_right()

    def rotate_right_left(self):
        self.right.rotate_right()
        self.rotate_left()

    # gets height from specific treeNode 
    def height(self):
        lheight = 0
        if self.left is not None:
            lheight = self.left.height()
        
        rheight = 0
        if self.right is not None:
            rheight = self.right.height()

        return 1 + max(rheight, lheight)
    
    # calculates the amount that the left height is greater than the right (neg ok) 
    def needBalance(self):
        lheight = 0
        if self.left is not None:
            lheight = self.left.height()
        rheight = 0
        if self.right is not None:
            rheight = self.right.height()

        return lheight - rheight

# An instance is a Binary Search Tree supporting methods such as insert, and find 
class Tree:
    def __init__(self):
        self.root = None
        
    # Recursive helper method to traverse
    def __traverse(self, node):
        if node is None:
            return ""
        
        l = self.__traverse(node.left)
        r = self.__traverse(node.right)
        
        return l + node.data.toString() + r
    
    # Executes in-order traversal of the elements in the tree, calling toString()
    def traverse(self):
        return self.__traverse(self.root).strip()

    # Checks for unbalance, and balances if necessary
    def __balance(self, node):
        bal = node.needBalance()
        
        # left overweighs right
        if bal > 1:
            if node.left.needBalance() > 0:
                node.rotate_right()
            else:
                node.rotate_left_right()

        # right overweighs left    
        elif bal < -1:
            if node.right.needBalance() < 0:
                node.rotate_left()
            else:
                node.rotate_right_left()
    
    # Recursive helper method to insert
    def __insert(self, node, str, filename, loc, desc):
        if node is None:
            p = Postings(str)
            p.add(filename, loc, desc)
            return TreeNode(p)
       
        # finds correct subtree to traverse via BST invariant
        if node.data.string > str:
            node.left = self.__insert(node.left, str, filename, loc, desc)
        elif node.data.string < str:
            node.right = self.__insert(node.right, str, filename, loc, desc)
        else:
            node.data.add(filename, loc, desc)
        
        # balance tree 
        if (use_avl_tree):
            self.__balance(node)
       
        return node

    # inserts given string into the tree, along with which file it was found,
    # the position inside the file, and a short description
    def insert(self, string, filename, loc, desc):
        if self.root is None:
            p = Postings(string)
            p.add(filename, loc, desc)
            self.root = TreeNode(p)
        else:
            self.__insert(self.root, string, filename, loc, desc)
    
    # recursive helper method to find
    def __find(self, node, str):
        if node is None:
            return None
        
        if node.data.string > str:
            return self.__find(node.left, str)
        elif node.data.string < str:
            return self.__find(node.right, str)
        else:
            return node
    
    # finds the given string inside the tree. Returns a treeNode or None
    def find(self, str):
        return self.__find(self.root, str)

# An instance keeps track of all of the indexing information associated with a 
# particular string found inside the corpus
class Postings:
    def __init__(self, s):
        self.string = s     # string we are interested in
        self.entries = {}   # <filename, locations> map
        self.desc = {}      # <filename, description string> map
    
    # inserts the filename, location, and description into current posting
    def add(self, filename, loc, desc):
        self.desc[filename] = desc
        try:
            entry = self.entries[filename]
        except KeyError:
            entry = []
        
        entry.append(loc)
        self.entries[filename] = entry
    
    # returns a verbose representation of the current posting
    def toString(self):
        s = self.string + "\n"
        for filename in sorted(self.entries.keys()):
            lstLoc = self.entries[filename]
            desc = self.desc[filename]

            s += "  " + filename + " [" + str(len(lstLoc)) + "]:"
            for loc in lstLoc:
                s += " " + str(loc)
            s += "\n"
            s += "  { ... " + desc + " ... }\n"
        return s

    # Returns TF: 1 + log(frequency)
    def __getTF(self, lstLoc):
        freq = len(lstLoc)
        return 1 + math.log10(freq)

    # Returns IDF: 1 + log(N/n)
    def __getIDF(self, num_docs):
        global total_docs
        return 1 + math.log10(total_docs/num_docs)
    
    # Returns TFIDF (used in multi-word searches)
    def getTFIDF(self, filename, term):
        global total_docs
        idf = self.__getIDF(len(self.entries.keys()))
        lst = self.entries[filename]
        tf = self.__getTF(lst)
        return tf * idf

    # returns a more concise representation of the current posting
    def toDisplay(self):
        s = ""
        sorted_filenames = sorted(self.entries.keys())
        num_docs = len(sorted_filenames)

        for filename in sorted_filenames:
            lstLoc = self.entries[filename]
            desc = self.desc[filename]
            
            tf = self.__getTF(lstLoc)
            idf = self.__getIDF(num_docs)
            tfidf = tf * idf

            s += filename + ": " + ",".join(map(lambda x: str(x), lstLoc)) + "\n"
            s += "tf: " + str(tf) + ", idf: " + str(idf) + ", tfidf: " + str(tfidf) + "\n"
            s += desc + "\n\n"

        return s

# Populates stoplist array with words from the stop list
def buildStopList(filename):
    stop_list = []
    for line in file(filename):
        stop_list.append(line.strip())
    return stop_list

# Given filename, iterates through text, and inserts text into index
def processFile(tree, filename):
    base = os.path.basename(filename)
    name, ext = os.path.splitext(base)
    
    visited_words = {}
    loc = 1
    for line in file(filename):
        arr = line.strip().split(" ")
      
        # for each word ... 
        for i in range(0,len(arr)):
            entry_orig = arr[i].strip()
            entry = entry_orig.lower()

            # Stop list check
            if entry not in stop_list:    
                desc = None
                if entry in visited_words:
                    desc = visited_words[entry]
                else:
                    words_remaining = 0
                    ctr = i-1
                    desc = entry_orig

                    # Generates REL_WORDS number of relevant words to cache
                    while (ctr >= 0 and words_remaining < REL_WORDS/2):
                        desc = arr[ctr] + " " + desc
                        words_remaining += 1
                        ctr -= 1

                    ctr = i + 1
                    while (ctr < len(arr) and words_remaining < REL_WORDS):
                        desc = desc + " " + arr[ctr]
                        words_remaining += 1
                        ctr += 1

                    visited_words[entry] = desc

                tree.insert(entry, name, loc, desc)
            loc += 1

# Builds Index
def buildTree(dir):
    global total_docs

    tree = Tree()
    files = glob.glob(dir + "/*.txt") 

    for f in files:
        processFile(tree, f)
        total_docs += 1
        print "Processed ", f

    return tree

# Returns TFIDF of given term in file
def getTFIDF(filename, term):
    node = tree.find(term)
    return node.data.getTFIDF(filename, term)

# Parser Options
parser = OptionParser()
parser.add_option("-d", action="store", type="string", dest="dir", help="Data Directory location")
parser.add_option("-s", action="store", type="string", dest="lst", help="StopList location")
parser.add_option("-a", action="store_true", dest="avl", default=False, help="Use AVL Self Balancing Tree")
(options, args) = parser.parse_args()

# User must submit files directory and stop list
if (options.dir == None or options.lst == None):
    print "Please run with directory option. (python main.py -d [data_dir] -s [stoplist])"
else:
    use_avl_tree = options.avl
    if use_avl_tree:
        print "Building balanced AVL Tree index."
    
    stop_list = buildStopList(options.lst)
    tree = buildTree(options.dir)
    print "Data loaded. Begin Querying"

    # Prompt the user for entry
    while 1:
        input = raw_input("Query: ")
        errormsg = "Your query {" + input + "} was not found."

        if (input == "ZZZ"):
            break
        elif len(input) is 0:
            print "Please input some text. Empty string doesn't count."
        else:
            query = input.split(" ")
            query = map(lambda x: x.lower(), query)
            print ""

            # Single word query
            if len(query) is 1:
                node = tree.find(query[0])
                if node is None:
                    print errormsg
                else:
                    print node.data.toDisplay().strip()
            
            # Multi word query
            else:
                input_filenames = []
                error = False

                for term in query:
                    node = tree.find(term)
                    if node is None:
                        error = True
                        break
                    else:
                        input_filenames.append(node.data.entries.keys())
                
                # If one of the terms not found in tree, display error
                if error:
                    print errormsg
                else:

                    # For each list of documents associated with a term, generate set
                    # Apply set intersection to all sets to get files with all terms
                    intersect = reduce(set.intersection, map(set, input_filenames))
                    
                    def sum_float (x,y):
                        return float(x) + float(y)
                    
                    results = []
                    
                    for filename in intersect:
                        
                        # append (filename, tfidf sum) to list
                        results.append((filename, reduce(sum_float, 
                            map(lambda term: getTFIDF(filename, term), query))))
                  
                    # sort list by tfidf value in decreasing order
                    results = sorted(results, key=lambda tuple: tuple[1])
                    results.reverse()

                    # display values
                    for item in results:
                        print item[0] + ": " + str(item[1])

            print ""
