from optparse import OptionParser
import sys
import glob
import os

REL_WORDS = 10
stop_list = []

class TreeNode:
    def __init__(self, d):
        self.left = None
        self.right = None
        self.data = d

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
   
    def __insert(self, node, str, filename, loc, desc):
        if node is None:
            p = Posting(str)
            p.add(filename, loc, desc)
            return TreeNode(p)
        
        if node.data.string > str:
            node.left = self.__insert(node.left, str, filename, loc, desc)
            return node
        elif node.data.string < str:
            node.right = self.__insert(node.right, str, filename, loc, desc)
            return node
        else:
            node.data.add(filename, loc, desc)
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
    tree = Tree()
    files = glob.glob(dir + "/*.txt") 

    for f in files:
        processFile(tree, f)

    return tree

parser = OptionParser()
parser.add_option("-d", "--dir", action="store", type="string", dest="dirname")
parser.add_option("-s", "--stoplist", action="store", type="string", dest="stoplist")
(options, args) = parser.parse_args()

if (options.dirname == None or options.stoplist == None):
    print "Please run with directory option. (python main.py -d [data_dir] -s [stoplist])"
else:
    stop_list = buildStopList(options.stoplist)
    tree = buildTree(options.dirname);
    done = False
   
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

            if len(query) is 1:
                node = tree.find(query[0])
                if node is None:
                    print errormsg
                else:
                    print node.data.toString().strip()
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