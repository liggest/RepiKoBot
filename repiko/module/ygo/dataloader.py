import functools
import sqlite3
import os
from enum import Enum
import typing

class ShrinkLevel(str,Enum):
    #TODO flag
    S0=""
    S1="type & 0x4000=0"
    S2="alias=0"
    S3="type & 0x48060C0=0"
    S4="type & 0x4802040!=0"
    
    No=S0
    NoToken=S1
    NoAlias=S2
    NoExtra=S3
    NoMain=S4

    @classmethod
    def fromInt(cls,i:typing.Union[int,'ShrinkLevel',typing.List[int]])-> 'ShrinkLevel':
        if isinstance(i,cls):
            return i
        if isinstance(i,list):
            return " AND ".join([cls.fromInt(x) for x in i if x]) # x!=0 and x!=S0
        return getattr(cls,f"S{i}")

    # @property
    # def WHERE(self):
    #     if self:
    #         return f"WHERE {self}"
    #     return self

def WHERE(s:str):
    if s:
        return f"WHERE {s}"
    return s

class cdbReader():

    def __init__(self,path=None):
        self.cdbpath=path
        self.conn=None
        self.cursor=None

    def __enter__(self):
        self.connect()
        # print("连上啦")
        return self
    
    def __exit__(self,etype,eval,traceback):
        # print("关掉啦")
        self.close()

    def connect(self,path=None):
        if path:
            self.conn=sqlite3.connect(path)
        elif self.cdbpath:
            self.conn=sqlite3.connect(self.cdbpath)
        else:
            raise Exception("no cdb path")
        if self.conn:
            self.cursor=self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
        else:
            raise Exception("no cdb connection")

    @staticmethod
    def listOfSQL(lens): # lens=3 -> (?,?,?)
        return "(" + ",".join(["?"]*lens) + ")"

    @staticmethod
    def unique(lst): # [111,111,222] -> [111,222]
        return list( set(lst) )

    def getCardByID(self,id): #id是整数
        self.cursor.execute("SELECT t.name,t.DESC,d.* FROM texts t INNER JOIN datas d ON t.id=d.id WHERE t.id=?",(id,))
        return self.cursor.fetchall()[0]

    def getCardsByIDs(self,*ids): #ids是元祖、列表之类的
        sql="SELECT t.name,t.DESC,d.* FROM texts t INNER JOIN datas d ON t.id=d.id WHERE t.id IN "
        sql+=cdbReader.listOfSQL(len(ids))
        self.cursor.execute(sql,tuple(ids) )
        return self.cursor.fetchall()

    def getIDsByName(self,name): #name是字符串 完全匹配
        self.cursor.execute("SELECT id FROM texts WHERE name=?",(name,))
        ids=self.cursor.fetchall()
        return [x[0] for x in ids]

    def getCardCount(self,shrink=0): #full 0 全部 1 无衍生物 2 无同名卡无衍生物
        level=ShrinkLevel.fromInt(shrink)
        self.cursor.execute(f"SELECT COUNT(*) FROM datas {WHERE(level)}")
        return self.cursor.fetchall()[0]

    def getRandomIDs(self,count=1,shrink=0):
        level=ShrinkLevel.fromInt(shrink)
        self.cursor.execute(f"SELECT id FROM datas {WHERE(level)} ORDER BY RANDOM() limit ?",(count,))
        ids=self.cursor.fetchall()
        return [x[0] for x in ids]

    def getRandomNames(self,count=1,shrink=0):
        ids=self.getRandomIDs(count,shrink)
        self.cursor.execute(f"SELECT name FROM texts WHERE id IN {cdbReader.listOfSQL(len(ids))}",tuple(ids))
        names=self.cursor.fetchall()
        return [x[0] for x in names]

    def getIDsByInput(self,ipt,expect=()):
        pass

    def getCardsByInput(self,ipt):
        pass

    def getYDCards(self):
        self.cursor.execute("SELECT id FROM datas WHERE type & 0x48060C0=0 ORDER BY RANDOM() limit 60")
        main=self.cursor.fetchall()
        main=[x[0] for x in main]
        self.cursor.execute("SELECT id FROM datas WHERE type & 0x4802040!=0 ORDER BY RANDOM() limit 30")
        extra=self.cursor.fetchall()
        extra=[x[0] for x in extra]
        return [main,extra]

class confReader():
    def __init__(self,path=None):
        self.filepath=path

    def loadLFlist(self,path=None):
        if path:
            self.filepath=path
        self.lfdict={}
        start=False
        with open(self.filepath,"r",encoding="utf-8") as f:
            for line in f:
                if start:
                    if line.startswith("!"):
                        break
                    if line[:1].isdigit():
                        temp=line.split()
                        self.lfdict[ int(temp[0]) ]=int(temp[1])
                else:
                    if line.startswith("!"):
                        self.lfname=line[1:]
                        start=True
    
    def loadSets(self,path=None):
        if path:
            self.filepath=path
        self.setdict={}
        with open(self.filepath,"r",encoding="utf-8") as f:
            for line in f:
                if line.startswith("!setname"):
                    temp=line.split()
                    self.setdict[ int(temp[1],base=16) ]=temp[2].split("\t")[0]


if __name__ == "__main__":

    conf=confReader()
    conf.loadLFlist("lflist.conf")
    conf.loadSets("strings.conf")
    #print(conf.lfname)
    #print(conf.lfdict)
    #print(conf.setdict)
    cdb=cdbReader()
    cdb.connect("cards.cdb")
    ipt=""
    #result=cdb.getCardsByIDs([1861629, 1861630])
    #print(result)
    '''
    while ipt!="exit":
        ipt=input()
        print( cdb.getIDsByName(ipt) )
        #try:
        #    
        #except:
        #    print("不好使")
    '''
    ids=cdb.getRandomIDs()
    cts=cdb.getCardsByIDs(*ids)
    #c=Card()
    #c.fromCDBTuple(cts[0],conf.setdict,conf.lfdict)
    #print( c )
    cdb.close()
