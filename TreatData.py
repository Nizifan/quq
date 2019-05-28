# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:33:18 2019

@author: shirley
"""

import pickle
import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
import requests
import telnetlib



def get_ip_list(headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'},url='http://www.xicidaili.com/wt'):
    """ 从代理网站上获取代理"""
    ip_list = []
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'lxml')
    ul_list = soup.find_all('tr', limit=200)
    
    for i in range(1, len(ul_list)):
        line = ul_list[i].find_all('td')
        ip = line[1].text
        port = line[2].text
        address = ip + ':' + port
        ip_list.append(address)
    return ip_list


def test_ip(IP_list):
    """ 测试IP是否可用 """
    isaval = np.zeros(len(IP_list))
    for i in range(len(IP_list)):
        #print('验证第'+str(i+1)+'个IP'+'(共'+str(len(IP_list))+'个IP)')
        ip = IP_list[i]
        hd, port = ip.split(':')
        try:
            telnetlib.Telnet(hd, port=port, timeout=5)
        except:
            isaval[i] = 0  # 失败
        else:
            isaval[i] = 1  # 成功
    IP_aval = [IP_list[k] for k in range(len(isaval)) if isaval[k]==1] 
    return IP_aval


def test_1_ip(ip):
    """ 验证一个IP """
    hd, port = ip.split(':')
    try:
        telnetlib.Telnet(hd, port=port, timeout=5)
    except:
        isavail = 0  # 失败
    else:
        isavail = 1  # 成功
    
    return isavail


def get_proxy(aip):
    """构建格式化的单个proxies"""
    proxy_ip = 'http://' + aip
    proxy_ips = 'https://' + aip
    proxy = {'https': proxy_ips, 'http': proxy_ip}
    return proxy




def LoadPkl(PathOfData,*arg):
    """ 下载PathOfData路径下名叫NameOfData的pickle文件 """
        
    if PathOfData[-3:]!='pkl':
        NameOfData = arg[0]
        file=open((PathOfData+NameOfData+'.pkl').encode('utf-8'), 'rb')
    else:
        file=open((PathOfData).encode('utf-8'), 'rb')
    
    data=pickle.load(file)
    file.close()
    
    return data


def SavePkl(PathOfData,data,NameOfData):
    """ 保存pickle数据
    PathOfData--保存的路径
    data--要保存的数据
    NameOfData--要保存的名称
    """
    
    output=open((PathOfData+NameOfData+'.pkl').encode('utf-8'), 'wb')
    pickle.dump(data, output)
    output.close()
    

def true_range(k_line):
    """ 计算真实波幅 
    * k_line : k线 high-最高价 low-最低价 open-开盘价 close-收盘价
    """
    
    tr = np.maximum(k_line.high.values-k_line.low.values,(k_line.high-k_line.close.shift(1)).abs().values,(k_line.low-k_line.close.shift(1)).abs().values)
    return tr


def EMA(data,window):
    """ data:numpy.array """
    
    ema = np.ones(len(data))*np.nan
    start = np.where(np.isnan(data)==0)[0][0]
    for t in range(start,len(data)):
        if t<start+window-1:
            ema[t] = data[t]
        else:
            ema[t] = data[t]*2/(window+1)+ema[t-1]*(window-1)/(window+1)
            if np.isnan(ema[t]):
                ema[t] = ema[t-1]
            
    return ema


def MACD(price,m=12,n=26,p=9):
    """MACD
    * m<n
    * m, n, p : 12,26,9
    """
    
    close = price.close.values
    EMA_m = EMA(close,m)    # 短均线
    EMA_n = EMA(close,n)    # 长均线
    DIFF = EMA_m-EMA_n
    DEA = EMA(DIFF,p)
    
    macd = DIFF-DEA
    
    return pd.DataFrame(np.column_stack([macd,DIFF,DEA]), index=price.index, columns=['MACD','DIF','DEA'])



def hbhy_settlement(account_name,params):
    """火币合约的结算规则
    """
    
    if account_name == '未实现盈亏':
        if params['合约张数'] == 0:
            ## 没有持仓就没有盈亏
            return 0
        else:
            return params['持仓方向']*(1/params['成本价']-1/params['最新价'])*params['合约张数']*params['合约面值']
    
    if account_name == '已实现盈亏':
        if params['合约张数'] == 0:
            ## 没有持仓就没有盈亏
            return 0
        else:
            return params['持仓方向']*(1/params['成本价']-1/params['平仓价'])*params['合约张数']*params['合约面值']
    
    if account_name == '保证金':
        ## 保证金随着最新价的变动而变动
        return params['合约面值']*params['合约张数']/params['最新价']/params['杠杆倍数']
    
    if account_name == '手续费':
        if params['合约张数'] == 0:
            return 0
        else:
            return (params['合约张数']*params['合约面值']/params['成交均价'])*params['费率']
    
    if account_name == '持仓均价':
        ## 相同的合约会进行仓位合并。平仓时，按照移动平均法计算成本
        if params['已开合约张数']==0:
            return params['新开合约成本价']
        else:
            return (params['已开合约张数']+params['新开合约张数'])/(params['已开合约张数']/params['已开合约成本价'] + params['新开合约张数']/params['新开合约成本价'])
        
    

