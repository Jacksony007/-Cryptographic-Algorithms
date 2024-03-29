"""
Adapted from: https://github.com/TejveerSingh13/Image-Steganography/blob/main/Code/huffman.py
"""
import heapq
from heapq import heappop, heappush
import sys
import re
import os
import pickle
from django.conf import settings

"""
Check if the given node is a leaf node in a binary tree.
Parameters:
	root (Node): The root node of the binary tree    
Returns:
	bool: True if the given node is a leaf node, False otherwise
"""
def isLeaf(root):
	# If the left and right child of the node are None, it is a leaf node
	return root.left is None and root.right is None


# This class represents a Node in a Huffman Tree
class Node:
	"""
	Initializes a Node with character ch, frequency freq, left and right child nodes.
	 Args:
    - ch: a character (can be None for internal nodes)
    - freq: an integer representing the frequency of the character in the input text
    - left: left child node (default: None)
    - right: right child node (default: None)
    """
	def __init__(self, ch, freq, left=None, right=None):
		self.ch = ch
		self.freq = freq
		self.left = left
		self.right = right

	"""
    Overrides the less than function to make `Node` work with priority queue.
    It ensures that the highest priority item has the lowest frequency.
    """
	def __lt__(self, other):
		return self.freq < other.freq


# This function is used to traverse the Huffman Tree and store Huffman Codes in a dictionary.
"""
Parameters:
	root: The root node of the Huffman Tree.
	s: A string variable which keeps track of the current Huffman code.
	huffman_code: A dictionary to store the Huffman codes of each character.
"""
def encode(root, s, huffman_code):

	# if root is None, return
	if root is None:
		return

	# if a leaf node is found, store its Huffman Code in the dictionary
	if isLeaf(root):
		huffman_code[root.ch] = s if len(s) > 0 else '1'

	# Recursively traverse the left and right subtree, adding '0' to the code for left subtree and '1' for right subtree
	encode(root.left, s + '0', huffman_code)
	encode(root.right, s + '1', huffman_code)


# This function encodes a given string using the Huffman coding algorithm.
"""
Parameters:
    text (str): The string to be encoded
"""


def encodeHuffman(text, textfile):
    # extract file name
	filename = textfile.split('.')[0]

	# Check if the given text is an empty string
	if len(text) == 0:
		return

	# Create a dictionary to store the frequency of each character in the text
	freq = {i: text.count(i) for i in set(text)}
    

	# Save the frequency dictionary to a file using pickle in media/data_freq/
	file_location = os.path.join(settings.MEDIA_ROOT, 'data_freq')
	os.makedirs(file_location, exist_ok=True)
 
	with open(os.path.join(file_location, f'{filename}_data_freq.pkl'), 'wb') as f:
		pickle.dump(freq, f)

	# Create a priority queue to store the live nodes of the Huffman tree
	pq = [Node(k, v) for k, v in freq.items()]
	heapq.heapify(pq)

	# Loop until there is more than one node in the priority queue
	while len(pq) != 1:

		# Remove the two nodes with the highest priority (the lowest frequency) from the priority queue
		left = heappop(pq)
		right = heappop(pq)

		# Create a new internal node with the two nodes as children and
		# with a frequency equal to the sum of the two nodes' frequencies
		total = left.freq + right.freq
		heappush(pq, Node(None, total, left, right))

	# `root` stores a pointer to the root of Huffman Tree
	root = pq[0]

	# Traverse the Huffman tree and store the Huffman codes in a dictionary
	huffmanCode = {}
	encode(root, '', huffmanCode)

	# Encode the given text using the Huffman codes
	s = ''
	for c in text:
		s += huffmanCode.get(c)
  
	return s

# This function decodes a given Huffman encoded string using the frequency table.
"""
Parameters:
	encodedString: The string to be decoded
	freq: The frequency table of characters used to encode the string
"""
def decodeHuffman(encodedString, freq):
    # Construct priority queue using the frequency table
    pq = [Node(k, v) for k, v in freq.items()]
    heapq.heapify(pq)

    # Reconstruct Huffman tree using the priority queue
    while len(pq) != 1:
        # Remove two nodes with lowest frequencies from queue
        left = heappop(pq)
        right = heappop(pq)
        total = left.freq + right.freq
        # Create new internal node with the two nodes as children
        heappush(pq, Node(None, total, left, right))

    # Get root node of Huffman tree
    root = pq[0]
    decodedString = ""

    # Traverse the Huffman tree to decode the encoded string by
    # moving left or right depending on the current bit
    index = 0  # Start index at 0
    while index < len(encodedString):
        current = root
        # Traverse tree until leaf node is reached or index exceeds length
        while not isLeaf(current) and index < len(encodedString):
            current = current.left if encodedString[index] == '0' else current.right
            index += 1
        if current.ch is not None:  # Check if current node is a leaf node
            decodedString += current.ch  # Concatenate only if current node has a character
    return decodedString

