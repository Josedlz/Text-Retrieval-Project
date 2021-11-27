from Classes.Buffer import Buffer
from helpers.sorting import mergeLists
from helpers.system import getSize

import os 
import json
import logging

from SPIMI_Inverter import SPIMI_Inverter   

class SPIMIIndexConstructor:
    def __init__(self):
        #Average block size
        self.blockSize = 0

        #Holds a mapping between words and blocks
        self.blocksMetaData = {}

        self.bufferA = Buffer({})
        self.bufferB = Buffer({})

        self.outputBuffer = {}

    def write_buffer(self, fileName, buffer):
        print("Writing", fileName)
        with open(fileName, 'w') as out:
            json.dump(buffer, out)

    def _getBlocksMetadata(self):
        objA = {}
        objA['filePath'] = self.bufferA.getFilePath()
        objA['fileSize'] = os.path.getsize(objA['filePath'])

        objB = {}
        objB['filePath'] = self.bufferB.getFilePath()
        objB['fileSize'] = os.path.getsize(objB['filePath'])

        return [objA, objB]

    def _loadBuffers(self, documentA, documentB):
        self.bufferA.load(documentA)
        self.bufferB.load(documentB)
        self.blocksMetaData = self._getBlocksMetadata() 
    
    def _addPostingList(self, word, postingList, currentOutputBlock, outputSizeLeft):
        postingListSize = getSize(postingList)
        ratio = outputSizeLeft//postingListSize

        if ratio >= 1 or currentOutputBlock['filePath'] == self.blocksMetaData[1]['filePath']:
            outputSizeLeft -= postingListSize
            self.outputBuffer[word] = postingList
        else:
            lastIndex = ratio*(len(postingList)-1)
            if lastIndex != 0:
                self.outputBuffer[word] = postingList[:lastIndex]
            self.write_buffer(currentOutputBlock['filePath'], self.outputBuffer)
            currentOutputBlock = self.blocksMetaData[1]
            outputSizeLeft = self.blocksMetaData[1]['fileSize']
            self.outputBuffer.clear()
            self.outputBuffer[word] = postingList[lastIndex:]
        
        return currentOutputBlock, outputSizeLeft

    def _sortBuffers(self):
        """
        I will iterate and constantly check three things
        1. Output buffer has not reached its max size yet
        2. Both buffers still have a current word
        3. Both buffers still have elements in the posting list
        of the current word that aren't assigned
        """
        currentOutputBlock = self.blocksMetaData[0]
        outputSizeLeft = currentOutputBlock['fileSize']

        i = 0
        j = 0

        n1 = self.bufferA.getLength()
        n2 = self.bufferB.getLength()

        while i < n1 and j < n2:
            wordA, postingListA = self.bufferA[i]
            wordB, postingListB = self.bufferB[j]

            if wordA == wordB:
                mergedPostingList = mergeLists(postingListA, postingListB)
                currentOutputBlock, outputSizeLeft = self._addPostingList(wordA, mergedPostingList, currentOutputBlock, outputSizeLeft)

            elif wordA < wordB:
                currentOutputBlock, outputSizeLeft = self._addPostingList(wordA, postingListA, currentOutputBlock, outputSizeLeft)

            else:
                currentOutputBlock, outputSizeLeft = self._addPostingList(wordB, postingListB, currentOutputBlock, outputSizeLeft)

            i += 1
            j += 1
        
        while i < n1:
            wordA, postingListA = self.bufferA[i]
            currentOutputBlock, outputSizeLeft = self._addPostingList(wordA, postingListA, currentOutputBlock, outputSizeLeft)
            i += 1
            
        while j < n2:
            wordB, postingListB = self.bufferB[j]
            self._addPostingList(wordB, postingListB, currentOutputBlock, outputSizeLeft)
            j += 1

        self.write_buffer(self.blocksMetaData[1]['filePath'], self.outputBuffer)
        self.outputBuffer.clear()
        return

    def merge(self, documents, l, m, r):
        L = documents[l : m+1]
        R = documents[m+1 : r+1]
        logging.info("Merging blocks:", L, "and", R)
        print("Merging blocks:", L, "and", R)

        for left, right in zip(L, R):
            logging.info("Comparing:", left, "and", right)
            print("Comparing:", left, "and", right)
            self._loadBuffers(left, right)
            self._sortBuffers()

    def mergeBlocks(self, documents, l, r):
        if l >= r:
            return 
        m = (l + r - 1) // 2
        self.mergeBlocks(documents, l, m)
        self.mergeBlocks(documents, m+1, r)
        self.merge(documents, l, m, r)


    def generate(self):
        """
        This method iterates over the documents by chunks
        of size documentSize.

        For each chunk of string, it creates a Pandas DataFrame. 

        Then it creates a dictionary using the document ID and the 
        content of the document. This is passed to an instance of the 
        Index Inverter class, using the same instance until its index 
        attribute exceeds blockSize.

        When this happens, we save the index created so far into a block
        of secondary memory, and then we free the memory of the Index Inverter
        class for it to keep iterating over the documents.
        """       

        root = os.getcwd()
        data_path = 'proyecto2/invertedindex/files/data_elecciones'
        path = os.path.join(root, data_path)

        for curFileNumber, file in enumerate(os.listdir(path)):
            with open(os.path.join(path, file), 'r') as f:
                data = json.load(f)
                spimi = SPIMI_Inverter(data, curFileNumber)   
                spimi.parseNextBlock()
                spimi.writeBlockToDisk()
    
if __name__ == '__main__':
    bsbi = SPIMIIndexConstructor()
    #bsbi.generate()
    path = os.getcwd()
    files = []
    for i in range(32):
        files.append(f"files/blocks/block_{i}.json")
    bsbi.mergeBlocks(files, 0, len(files)-1)
    print("termine bitch")
    
