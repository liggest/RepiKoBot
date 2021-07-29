import random
class Calculator():
    symbol=["+","-","*","/","(",")"]
    def __init__(self):
        pass
    def cal(self,s):
        if self.isnumber(s[0]):
            return s
        elif s[0]=="error":
            return ["error",s[1]]
        elif "(" in s[0] or ")" in s[0]: #or "^" in s[0]:
            el=self.analyze(s)
            e=el[0]
            log=el[1]
            return self.cal([e,log])
        else:
            e=s[0]
            log=s[1]
            if "-" in e:
                ex=e
                for x in range(len(e)):
                    if e[x]=="-":
                        if x==0:
                            ex="–"+ex[1:]
                        elif e[x-1] in self.symbol:
                            ex=ex[:x]+"–"+ex[x+1:]
                e=ex
            if "*" in e or "/" in e:
                length=len(e)
                lastMark=-1
                thisMark=0
                nextMark=length
                mark="*"
                for x in range(length):
                    if e[x]=="*" or e[x]=="/":
                        thisMark=x
                        mark=e[x]
                        for y in range(thisMark+1,length):
                            if e[y] in self.symbol:
                                nextMark=y
                                break
                        for y in range(thisMark-1,-1,-1):
                            if e[y] in self.symbol:
                                lastMark=y
                                break
                        target_l=e[lastMark+1:thisMark].replace("–","-")
                        target_r=e[thisMark+1:nextMark].replace("–","-")
                        if not self.isnumber(target_l):
                            target=self.cal([target_l,log])
                            target_l=target[0]
                            log=target[1]
                        if not self.isnumber(target_r):
                            target=self.cal([target_r,log])
                            target_r=target[0]
                            log=target[1]
                        if target_r=="error" or target_l=="error":
                            return ["error",log]
                        if mark=="*":
                            result_temp=str(float(target_l)*float(target_r))
                        elif mark=="/" and target_r!="0":
                            result_temp=str(float(target_l)/float(target_r))
                        else:
                            return ["error",log]
                        e=e[:lastMark+1]+result_temp+e[nextMark:]
                        log=log+e+"\n"
                        break
            elif "+" in e or "-" in e:
                length=len(e)
                lastMark=-1
                thisMark=0
                nextMark=length
                mark="+"
                for x in range(length):
                    if e[x]=="+" or e[x]=="-":
                        thisMark=x
                        mark=e[x]
                        for y in range(thisMark+1,length):
                            if e[y] in self.symbol:
                                nextMark=y
                                break
                        for y in range(thisMark-1,-1,-1):
                            if e[y] in self.symbol:
                                lastMark=y
                                break
                        target_l=e[lastMark+1:thisMark].replace("–","-")
                        target_r=e[thisMark+1:nextMark].replace("–","-")
                        if not self.isnumber(target_l):
                            target=self.cal([target_l,log])
                            target_l=target[0]
                            log=target[1]
                        if not self.isnumber(target_r):
                            target=self.cal([target_r,log])
                            target_r=target[0]
                            log=target[1]
                        if target_r=="error" or target_l=="error":
                            return ["error",log]
                        if mark=="+":
                            result_temp=str(float(target_l)+float(target_r))
                        elif mark=="-":
                            result_temp=str(float(target_l)-float(target_r))
                        else:
                            return ["error",log]
                        e=e[:lastMark+1]+result_temp+e[nextMark:]
                        log=log+e+"\n"
                        break
            else:
                return ["error",log]
            return self.cal([e,log])
                    
    def analyze(self,s):
        e=s[0]
        log=s[1]
        while "(" in e or ")" in e:
            bracketL=0
            bracketR=0
            length=len(e)
            for x in range(length-1,-1,-1):
                if e[x]=="(":
                    bracketL=x
                    bracketR=e[x:].find(")")+x
                    break
            rs=e[bracketL+1:bracketR]
            log=log+rs+"\n"
            result_temp=self.cal([rs,log])
            if result_temp[0]=="error":
                return ["error",result_temp[1]]
            e=e[:bracketL]+result_temp[0]+e[bracketR+1:]
            log=result_temp[1]+e+"\n"  
        return [e,log]
    def isnumber(self,s):
        try :
            float(s)
            return True
        except:
            return False
    def dice(self,s):
        e=s
        while "d" in e:
            length=len(e)
            dn=e.find("d")
            start=-1
            end=length
            for x in range(dn+1,length):
                if not e[x].isdecimal():
                    end=x
                    break
            for y in range(dn-1,-1,-1):
                if not e[y].isdecimal():
                    start=y
                    break
            startn=e[start+1:dn]
            endn=e[dn+1:end]
            if startn=="":
                startn=1
            else:
                startn=abs(int(startn))
            if endn=="":
                endn=100
            else:
                endn=abs(int(endn))
            if endn!=0 and startn<=100 and startn!=0:
                result_temp="("
                for z in range(startn):
                    result_temp+=str(random.randint(1,endn))
                    if z!=startn-1:
                        result_temp+="+"
                result_temp+=")"
            elif endn==0:
                return "-丢了个卵子"
            elif startn>100:
                return "-丢了一群卵子"
            elif startn==0:
                return "-丢不出卵子，只能丢人了"
            e=e[:start+1]+result_temp+e[end:]
        return e
    def dicetext(self,s,act):
        text=self.dice(s)
        if text[0:2]=="-丢":
            return text[1:]
        num=self.cal([text,text+"\n"])
        if num[0]!="error":
            return "投掷 "+act+" :"+s+" = "+text+" = "+num[0]
        else:
            return "呜…投个骰子都卡住了……"
#x=Calculator()
#a=input()
#r=x.cal([a,a+"\n"])
#print(r[1][:-1])
#if r[0]=="error":
#    print("error")
#print(x.dicetext(a,""))
