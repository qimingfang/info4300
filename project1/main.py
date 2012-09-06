from optparse import OptionParser
import sys
import glob
import os
import math

REL_WORDS = 10
use_avl_tree = False
total_docs = 0
stop_list = []

class TreeNode:
    def __init__(self, d):
        self.left = None
        self.right = None
        self.data = d

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

    def height(self):
        lheight = 0
        if self.left is not None:
            lheight = self.left.height()
        
        rheight = 0
        if self.right is not None:
            rheight = self.right.height()

        return 1 + max(rheight, lheight)

    def needBalance(self):
        lheight = 0
        if self.left is not None:
            lheight = self.left.height()
        rheight = 0
        if self.right is not None:
            rheight = self.right.height()

        return lheight - rheight

class Tree:
    def __init__(self):
        self.root = None
        self.num_vals = None

    def __traverse(self, node):
        if node is None:
            return ""
        
        l = self.__traverse(node.left)
        r = self.__traverse(node.right)
        
        return l + node.data.toString() + r

    def traverse(self):
        return self.__traverse(self.root).strip()

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

    def __insert(self, node, str, filename, loc, desc):
        if node is None:
            p = Posting(str)
            p.add(filename, loc, desc)
            return TreeNode(p)
        
        if node.data.string > str:
            node.left = self.__insert(node.left, str, filename, loc, desc)
        elif node.data.string < str:
            node.right = self.__insert(node.right, str, filename, loc, desc)
        else:
            node.data.add(filename, loc, desc)
        
        if (use_avl_tree):
            self.__balance(node)
       
        return node

    # inserts given string into the tree
    def insert(self, str, filename, loc, desc):
        if self.root is None:
            p = Posting(str)
            p.add(filename, loc, desc)
            self.root = TreeNode(p)
        else:
            self.__insert(self.root, str, filename, loc, desc)
    
    # = Posting object for string.
    # = None if not found
    def __find(self, node, str):
        if node is None:
            return None
        
        if node.data.string > str:
            return self.__find(node.left, str)
        elif node.data.string < str:
            return self.__find(node.right, str)
        else:
            return node

    def find(self, str):
        return self.__find(self.root, str)

class Posting:
    def __init__(self, s):
        self.string = s
        self.entries = {}
        self.desc = {}
    def add(self, filename, loc, desc):
        self.desc[filename] = desc
        try:
            entry = self.entries[filename]
        except KeyError:
            entry = []
        
        entry.append(loc)
        self.entries[filename] = entry
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
    def __getTF(self, lstLoc):
        freq = len(lstLoc)
        return 1 + math.log10(freq)
    def __getIDF(self, num_docs):
        global total_docs
        return 1 + math.log10(total_docs/num_docs)
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

            s += ",".join([str(tf), str(idf), str(tfidf)]) + "\n"
            s += filename + "," + ",".join(map(lambda x: str(x), lstLoc)) + "\n"
            s += desc + "\n"

        return s

def buildStopList(filename):
    stop_list = []
    for line in file(filename):
        stop_list.append(line.strip())
    return stop_list

def processFile(tree, filename):
    base = os.path.basename(filename)
    name, ext = os.path.splitext(base)
    
    visited_words = {}
    loc = 1
    for line in file(filename):
        arr = line.strip().split(" ")
      
        for i in range(0,len(arr)):
            entry_orig = arr[i].strip()
            entry = entry_orig.lower()

            if entry not in stop_list:    
                desc = None
                if entry in visited_words:
                    desc = visited_words[entry]
                else:
                    words_remaining = 0
                    ctr = i-1
                    desc = entry_orig
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

def buildTree(dir):
    global total_docs

    tree = Tree()
    files = glob.glob(dir + "/*.txt") 

    for f in files:
        processFile(tree, f)
        total_docs += 1
        print "Processed ", f

    return tree

parser = OptionParser()
parser.add_option("-d", action="store", type="string", dest="dir", help="Data Directory location")
parser.add_option("-s", action="store", type="string", dest="lst", help="StopList location")
parser.add_option("-a", action="store_true", dest="avl", default=False, help="Use AVL Self Balancing Tree")
(options, args) = parser.parse_args()

if (options.dir == None or options.lst == None):
    print "Please run with directory option. (python main.py -d [data_dir] -s [stoplist])"
else:
    use_avl_tree = options.avl
    if use_avl_tree:
        print "Building balanced AVL Tree index."
    
    stop_list = buildStopList(options.lst)
    tree = buildTree(options.dir)
    print "Data loaded. Begin Querying"

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

            if len(query) is 1:
                node = tree.find(query[0])
                if node is None:
                    print errormsg
                else:
                    print node.data.toDisplay().strip()
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
                
                if error:
                    print errormsg
                else:
                    intersect = reduce(set.intersection, map(set, input_filenames))
                    print intersect

            print ""
