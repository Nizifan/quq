# -*- coding: utf-8 -*-
"""
Created on Tue May 14 16:28:09 2019

@author: shirley
"""

import os
os.chdir("G:\BTC")
path = 'G:/BTC/'

import copy
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
from HuobiDMService import HuobiDM
from pprint import pprint

#### input huobi dm url
URL = ''

####  input your access_key and secret_key below:
ACCESS_KEY = ''
SECRET_KEY = ''


dm = HuobiDM(URL, ACCESS_KEY, SECRET_KEY)


def LoadPkl(path,*arg):
    """ 下载path路径下名叫name的pickle文件 """
        
    if path[-3:]!='pkl':
        NameOfData = arg[0]
        file=open((path+NameOfData+'.pkl').encode('utf-8'), 'rb')
    else:
        file=open((path).encode('utf-8'), 'rb')
    
    data=pickle.load(file)
    file.close()
    
    return data


def SavePkl(path,data,name):
    """ 保存pickle数据
    path--保存的路径
    data--要保存的数据
    NameOfData--要保存的名称
    """
    
    output=open((path+name+'.pkl').encode('utf-8'), 'wb')
    pickle.dump(data, output)
    output.close()




def true_range(k_line):
    """ 计算真实波幅 
    * k_line : k线 high-最高价 low-最低价 open-开盘价 close-收盘价
    """
    
    tr = np.maximum(k_line.high.values-k_line.low.values,(k_line.high-k_line.close.shift(1)).abs().values,(k_line.low-k_line.close.shift(1)).abs().values)
    return tr



def DochianRange(k_line,w1=20,w2=10,max_add_times=3,sl_range=2,add_range=0.5,big_float=6,draw_back=1):
    """ 唐奇安通道--海龟交易 
    w1 : 开仓线窗口长度
    w2 : 平仓线窗口长度
    max_add_times : 最大加仓次数 默认最多加仓3次
    sl_range : stop loss的宽度，默认2倍ATR止损
    add_range : 加仓的宽度，默认0.5倍ATR加仓
    big_float和draw_back : 止盈幅度，默认价格冲破6倍ATR后回落1倍ATR则止盈（追踪止盈）
    """
    
    up_l = k_line.high.rolling(w1).max().shift(1).values  # 长期高价 -- 做多线
    dn_l = k_line.low.rolling(w1).min().shift(1).values   # 长期低价 -- 做空线
    
    up_s = k_line.high.rolling(w2).max().shift(1).values  # 短期高价 -- 平空线
    dn_s = k_line.low.rolling(w2).min().shift(1).values   # 短期低价 -- 平多线
    
    signals = pd.DataFrame(np.zeros([len(k_line),4]),index=k_line.index,columns=['open_long','open_short','close_long','close_short'])
    
    flag = 0           # 仓位状态初始化,初始无持仓
    basis_price = 0    # 止盈止损基准价初始化
    add_times = 0      # 加仓次数初始化
    open_point = 0     # 开仓时间初始化
    
    for t in range(w1,len(k_line)):
        time = k_line.index[t]   # 当前时间
        
        isOpenLong = k_line.close.iloc[t] > up_l[t] and k_line.close.iloc[t-1] <= up_l[t-1]   # 上穿长上轨--做多
        isOpenShort = k_line.close.iloc[t] < dn_l[t] and k_line.close.iloc[t-1] >= dn_l[t-1]  # 下穿长下轨--做空
        
        isCloseLong = k_line.close.iloc[t] < dn_s[t]                                           # 做多后价格跌破短期低价则平仓(止盈止损)
        isCloseShort = k_line.close.iloc[t] > up_s[t]                                          # 做空后价格涨回短期高价则平仓(止盈止损)
        
        if flag == 1:
            """ 若持有多单 """
            isStopLoss = k_line.close.iloc[t] <= basis_price-sl_range*k_line.ATR.iloc[t]   # 价格跌破止损价
            isAdd = k_line.close.iloc[t] >= basis_price+add_range*k_line.ATR.iloc[t]       # 价格涨到加仓价
            isStopProfit = k_line.loc[open_point:time,'close'].max() - basis_price >= big_float*k_line.ATR.iloc[t] \
                           and k_line.loc[open_point:time,'close'].max() - k_line.close.iloc[t] >= draw_back*k_line.ATR.iloc[t]  # 盈利高点回撤
            
            if (isStopLoss or isStopProfit or isCloseLong) and isOpenLong==0:
                # 止损或止盈或正常出仓(且避免平仓后同向开仓)
                flag = 0                              # 仓位状态重置
                add_times = 0                         # 加仓次数重置
                signals.loc[time,'close_long'] = 1    # 平多单标记

            else:
                if isAdd and add_times < max_add_times:
                    # 加仓
                    basis_price = k_line.close.iloc[t]  # 更新止盈止损基准价
                    add_times += 1                      # 加仓次数增加
                    open_point = k_line.index[t]        # 更新开仓时间
                    signals.loc[time,'open_long'] = 1   # 做多标记
        
        if flag == -1:
            """ 持空单 """
            isStopLoss = k_line.close.iloc[t] >= basis_price+sl_range*k_line.ATR.iloc[t]   # 价格涨到止损价
            isAdd = k_line.close.iloc[t] <= basis_price-add_range*k_line.ATR.iloc[t]       # 价格跌破加仓价
            isStopProfit = basis_price - k_line.loc[open_point:time,'close'].min() >= big_float*k_line.ATR.iloc[t] \
                           and k_line.close.iloc[t] - k_line.loc[open_point:time,'close'].min() >= draw_back*k_line.ATR.iloc[t]  # 盈利高点回撤
            
            if (isStopLoss or isStopProfit or isCloseShort) and isOpenShort==0:
                # 平仓
                flag = 0
                add_times = 0
                signals.loc[time,'close_short'] = 1

            else:
                if isAdd and add_times < max_add_times:
                    # 加仓
                    basis_price = k_line.close.iloc[t]
                    add_times += 1
                    open_point = k_line.index[t]
                    signals.loc[time,'open_short'] = 1
            
        if flag == 0:
            """ 无持仓 """
            if isOpenLong:
                # 做多
                flag = 1
                open_point = k_line.index[t]         # 开仓时间
                basis_price = k_line.close.iloc[t]   # 止盈止损基准价
                signals.loc[time,'open_long'] = 1    # 做多标记
                
            elif isOpenShort:
                # 做空
                flag = -1
                open_point = k_line.index[t]
                basis_price = k_line.close.iloc[t]   # 止盈止损基准价
                signals.loc[time,'open_short'] = 1   # 做空标记
    
    return signals


def BollRobber(k_line,w1=50,a=1,w2=30,w3=10,sl_range=2,big_float=6,draw_back=1):
    """布林强盗
    """
    
    up1 = k_line.close.rolling(w1).mean() + a*k_line.close.rolling(w1).std()  # 上轨1--布林带
    dn1 = k_line.close.rolling(w1).mean() - a*k_line.close.rolling(w1).std()  # 下轨1--布林带
    
    up2 = k_line.close.rolling(w2).max().shift(1)                             # 上轨2 -- 前期收盘价高点
    dn2 = k_line.close.rolling(w2).min().shift(1)                             # 下轨2 -- 前期收盘价低点
    
    flag = 0
    hold_day = 0
    open_price = 0
    open_index = 0
    signal = pd.DataFrame(np.zeros([len(k_line),4]),index=k_line.index,columns=['open_long','open_short','close_long','close_short'])
    
    for t in range(max(w1,w2),len(k_line)):
        time = k_line.index[t]
        isOpenLong = k_line.close.iloc[t] > max(up1.iloc[t],up2.iloc[t]) and k_line.close.iloc[t-1]<=max(up1.iloc[t-1],up2.iloc[t-1])
        isOpenShort = k_line.close.iloc[t] < min(dn1.iloc[t],dn2.iloc[t]) and k_line.close.iloc[t-1] >= min(dn1.iloc[t-1],dn2.iloc[t-1])
        
        if flag == 1:
            """ 当前有多单 """
            x = max(w3,w1-hold_day)                           # 平仓价计算周期
            stop_price = k_line.close.iloc[t-x+1:t+1].mean()  # 更新出场MA
            # 价格跌破自适应均线且自适应均线小于上轨
            isExit = k_line.close.iloc[t] < stop_price and stop_price < up1.iloc[t]  
            # 价格跌破止损价
            isStopLoss = k_line.close.iloc[t] <= open_price-sl_range*k_line.ATR.iloc[t]  
            # 跟踪止盈
            y = k_line.close.iloc[open_index:t].max()
            isStopProfit = y - open_price >= big_float*k_line.ATR.iloc[t] and y - k_line.close.iloc[t]>=draw_back*k_line.ATR.iloc[t] 

            if (isExit or isStopLoss or isStopProfit) and isOpenLong==0:
                ## 平掉多单
                flag = 0
                signal.loc[time,'close_long'] = 1
            else:
                hold_day += 1                         # 持有天数加1
        
        if flag == -1:
            """ 当前有空单 """
            x = max(w3,w1-hold_day)                           # 平仓价计算周期
            stop_price = k_line.close.iloc[t-x+1:t+1].mean()  # 更新出场MA
            # 价格涨到自适应均线且自适应均线大于下轨
            isExit = k_line.close.iloc[t] > stop_price and stop_price > dn1.iloc[t]   
            # 止损
            isStopLoss = k_line.close.iloc[t] >= open_price+sl_range*k_line.ATR.iloc[t]
            # 止盈
            y = k_line.close.iloc[open_index:t].min()
            isStopProfit = open_price - y >= big_float*k_line.ATR.iloc[t] and k_line.close.iloc[t] - y >= draw_back*k_line.ATR.iloc[t] 

            if (isExit or isStopLoss or isStopProfit) and isOpenShort==0:
                ## 平掉空单
                flag = 0
                signal.loc[time,'close_short'] = 1
            else:
                hold_day += 1                         # 持有天数加1 
                
        if flag == 0:
            """ 当前无持仓 """
            if isOpenLong:
                ## 做多 -- 价格上穿上轨和近期最高价
                hold_day = 0
                flag = 1
                signal.loc[time,'open_long'] = 1
                stop_price = k_line.close.iloc[t-w1+1:t+1].mean()   # 首日出场MA
                open_price = k_line.close[t]                        # 止盈止损基准价
                open_index = copy.deepcopy(t)
                
            if isOpenShort:
                ## 做空 -- 价格下穿下轨和近期最低价
                hold_day = 0
                flag = -1
                signal.loc[time,'open_short'] = 1
                stop_price = k_line.close.iloc[t-w1+1:t+1].mean()  # 首日出场MA
                open_price = k_line.close.iloc[t]                  # 止盈止损基准价
                open_index = copy.deepcopy(t)
    
    return signal
    


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
        
    

def get_pnl_hbhy(k_line,signals,initial_eqt=1,face_val=100,min_move=0.01,slip=1,risk_expo=0.01,lvg=2,fee=3e-4):
    """火币合约hbhy的盈亏计算
    k_line : k线
    signals : 开平信号
    initial_eqt : 初始权益--以币的数量计,默认初始1颗币
    face_val : 合约面值--BTC合约面值100刀
    min_move : 价格最小变动单位--BTC合约最小变动0.01刀
    slip : 默认成交的滑点是1个最小变动单位
    risk_expo : 风险暴露，默认取0.01
    lvg : 杠杆倍数,默认2倍
    fee : 手续费
    
    下单时间和价格：第T根Bar给出下单信号后，第T+1根Bar开盘时刻下单;
                   下单方式：对手价下单（实盘的时候只需要输入下单数量，无需输入下单价格，系统自动下达对手价的限价委托）
                   回测程序若不存在对手价数据，则假设以T+1根Bar的(开盘价+slip*min_move)成交（BTC的价格最小变动单位是0.01）
    
    合约账户权益 = 账户余额 + 本周已实现盈亏+本周未实现盈亏
    周五清算后，已实现盈亏计入账户余额; 回测程序假设已实现盈亏直接计入账户余额
    账户余额分为保证金和现金(均以币计)
    """
        
    pnl = pd.DataFrame(columns=['合约张数','开仓价','平仓价','成本价','总权益','现金','保证金','未实现盈亏','已实现盈亏','手续费'])
    pnl.loc[k_line.index[0]] = 0
    pnl.loc[k_line.index[0],['总权益','现金']] = initial_eqt
    
    for t in range(1,len(k_line)):
        unit = pnl.总权益.iloc[t-1]*risk_expo*(k_line.close.iloc[t-1]**2)/face_val/k_line.ATR.iloc[t-1] # 最多开仓合约张数
        unit = np.round(max(unit,1))  # 合约张数取整
        
        time = k_line.index[t]
        pnl.loc[time] = 0             # 初始化账户值
        
        if signals.open_long.iloc[t-1] == 1:
            ## 做多信号
            if signals.close_short.iloc[t-1] == 1:
                ## 平空的同时做多
                pnl.loc[time,'合约张数'] = unit
                pnl.loc[time,['开仓价','平仓价','成本价']] = k_line.open.iloc[t] + slip*min_move  # 开盘价+滑点
                pnl.loc[time,'已实现盈亏'] = hbhy_settlement('已实现盈亏', {'持仓方向':-1,'成本价':pnl.成本价.iloc[t-1],'平仓价':pnl.平仓价.iloc[t],'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val})
                pnl.loc[time,'手续费'] = hbhy_settlement('手续费', {'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val,'成交均价':pnl.平仓价.iloc[t],'费率':fee})  # 平仓手续费
                pnl.loc[time,'手续费'] += hbhy_settlement('手续费', {'合约张数':np.abs(pnl.合约张数.iloc[t]),'合约面值':face_val,'成交均价':pnl.开仓价.iloc[t],'费率':fee})   # 开仓手续费

            else:
                ## 单纯做多: (1)新建多仓 (2)加仓
                pnl.loc[time,'合约张数'] = pnl.合约张数.iloc[t-1]+unit
                pnl.loc[time,'开仓价'] = k_line.open.iloc[t]+slip*min_move  # 开盘价+滑点
                pnl.loc[time,'成本价'] = hbhy_settlement('持仓均价', {'已开合约张数':pnl.合约张数.iloc[t-1],'新开合约张数':unit,'已开合约成本价':pnl.成本价.iloc[t-1],'新开合约成本价':pnl.开仓价.iloc[t]})
                pnl.loc[time,'手续费'] = hbhy_settlement('手续费', {'合约张数':unit,'合约面值':face_val,'成交均价':pnl.开仓价.iloc[t],'费率':fee})
        
        elif signals.open_short.iloc[t-1] == 1:
            ## 做空信号
            if signals.close_long.iloc[t-1] == 1:
                ## 平多的同时开空
                pnl.loc[time,'合约张数'] = -unit
                pnl.loc[time,['开仓价','平仓价','成本价']] = k_line.open.iloc[t] - slip*min_move  # 开盘价-滑点
                pnl.loc[time,'已实现盈亏'] = hbhy_settlement('已实现盈亏', {'持仓方向':1,'成本价':pnl.成本价.iloc[t-1],'平仓价':pnl.平仓价.iloc[t],'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val})
                pnl.loc[time,'手续费'] = hbhy_settlement('手续费', {'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val,'成交均价':pnl.平仓价.iloc[t],'费率':fee})  # 平仓手续费
                pnl.loc[time,'手续费'] += hbhy_settlement('手续费', {'合约张数':np.abs(pnl.合约张数.iloc[t]),'合约面值':face_val,'成交均价':pnl.开仓价.iloc[t],'费率':fee})   # 开仓手续费
            else:
                ## 单纯做空: (1)新建空仓 (2)加仓
                pnl.loc[time,'合约张数'] = pnl.合约张数.iloc[t-1]-unit
                pnl.loc[time,'开仓价'] = k_line.open.iloc[t]-slip*min_move  # 开盘价+滑点
                pnl.loc[time,'成本价'] = hbhy_settlement('持仓均价', {'已开合约张数':np.abs(pnl.合约张数.iloc[t-1]),'新开合约张数':unit,'已开合约成本价':pnl.成本价.iloc[t-1],'新开合约成本价':pnl.开仓价.iloc[t]})
                pnl.loc[time,'手续费'] = hbhy_settlement('手续费', {'合约张数':unit,'合约面值':face_val,'成交均价':pnl.开仓价.iloc[t],'费率':fee})
        
        else:
            ## 没有开仓信号
            if signals.close_long.iloc[t-1] == 1 and pnl.合约张数.iloc[t-1]>0:
                ## 平多单信号
                pnl.loc[time,'平仓价'] = k_line.open.iloc[t] - slip*min_move
                pnl.loc[time,'已实现盈亏'] = hbhy_settlement('已实现盈亏', {'持仓方向':1,'成本价':pnl.成本价.iloc[t-1],'平仓价':pnl.平仓价.iloc[t],'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val})
                pnl.loc[time,'手续费'] = hbhy_settlement('手续费', {'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val,'成交均价':pnl.平仓价.iloc[t],'费率':fee})  # 平仓手续费
                
            elif signals.close_short.iloc[t-1] == 1 and pnl.合约张数.iloc[t-1]<0:
                ## 平空信号
                pnl.loc[time,'平仓价'] = k_line.open.iloc[t] + slip*min_move
                pnl.loc[time,'已实现盈亏'] = hbhy_settlement('已实现盈亏', {'持仓方向':-1,'成本价':pnl.成本价.iloc[t-1],'平仓价':pnl.平仓价.iloc[t],'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val})
                pnl.loc[time,'手续费'] = hbhy_settlement('手续费', {'合约张数':np.abs(pnl.合约张数.iloc[t-1]),'合约面值':face_val,'成交均价':pnl.平仓价.iloc[t],'费率':fee})  # 平仓手续费

            else:
                ## 无操作
                pnl.loc[time,['合约张数','成本价']] = pnl[['合约张数','成本价']].iloc[t-1].values  # 合约张数和成本价不变
                
        
        ## 通用算法账户
        pnl.loc[time,'未实现盈亏'] = hbhy_settlement('未实现盈亏', {'持仓方向':np.sign(pnl.loc[time,'合约张数']),'成本价':pnl.loc[time,'成本价'],'最新价':k_line.loc[time,'close'],'合约张数':np.abs(pnl.loc[time,'合约张数']),'合约面值':face_val})
        pnl.loc[time,'保证金'] = hbhy_settlement('保证金', {'合约面值':face_val,'合约张数':np.abs(pnl.loc[time,'合约张数']),'最新价':k_line.loc[time,'close'],'杠杆倍数':lvg})
        pnl.loc[time,'现金'] = pnl.现金.iloc[t-1] - (pnl.保证金.iloc[t]-pnl.保证金.iloc[t-1]) - pnl.loc[time,'手续费'] + pnl.loc[time,'已实现盈亏']
        pnl.loc[time,'总权益'] = pnl.现金.iloc[t] + pnl.保证金.iloc[t] + pnl.未实现盈亏.iloc[t]
    
    return pnl

def give_order(type_of_trade):
    if type_of_trade == "buy"：
        bid_order()
    elif type_of_trade == "sell"：
        sell_order()
    else:
        return false

def buy_order(amount, price, type_of_trade):
    ret = give_order_request(ACCOUNT_ID, amount, price, SOURCE, SYMBOL, type_of_trade)
    order_id = ret["data"]["order_id"]
    is_bid = type_of_trade == "" or type_of_trade == ""
    
    wait_count = 5
    while 1:
        time.sleep(1)
        order_info = get_order(order_id)
        if order_info["data"][0]["volume"] == order_info["data"][0]["trade_volumn"]:
            if type_of_trade == buy:
                FILLED_ORDER.add(order_info)
            else:
                FILLED_ORDER.minus(order_info)
            return 0
        else:
            if wait_count > 0:
                wait_count -= 1
                continue
            else:
                while 1:
                    ret = cancel_order(order_id)
                    if ret["status"] == "fail":
                        time.sleep(1)
                        continue
                    else:
                        ret_ = get_order[order_id]
                        if ret["data"]["success"][0] == order_id or ret_["data"]["status"] == "5" or ret["data"]["status"] == "7":
                            if ret["data"]["trade_volume"] != 0:
                                amount = ret_["data"]["volume"] - ret["data"]["trade_volume"]
                                FILLED_ORDER.add(order_id, ret["data"]["trade_avg_price"], ret["data"]["trade_volumn"], ret["data"]["fee"])
                            order_id = give_order_request(ACCOUNT_ID, amount, price, SOURCE, SYMBOL, type_of_trade)["data"]["order_id"]
                            wait_count = 5
                            break
                        elif ret_["data"]["status"] == "6":
                            return 0
                        else：
                            time.sleep(1)
                        
                                
                    
            '''
            ret = get_contract_depth(SYMBOL)[bid]
            target = ret["bids"][0] if type_of_trade == "buy" else ret["asks"][0]
            if(abs(target - price) > DELTA_VALUE):
                price = target
                max_retry += 1
                if max_retry > 3:
                    return 3
                cancel_order(order_id)
                ret = give_order_request(ACCOUNT_ID, amount, price , SOURCE, SYMBOL, type_of_trade)
                order_id = ret["data"]
                '''

def sell_order(,clear_all):
    if clear_all:
        to_sell = KEPY_ORDER
    else:
        to_sell = order_id

                

def write_log(log_file, string, ts):
    log_file.write(string(time.time()) + ":ts" + ts + ":string")

def CheckWhetherCancelOrders():

def main:

    #initialization
    global LOG_FILE_VERBOSE = file.open("Log_Verbose.txt")
    global LOG_FILE_STATUS = file.open("Log_Status.txt")
    global LOG_FILE_ERROR = file.open("Log_Error.txt")
    #global CONFIG_FILE = file.open("Delta_Config.txt")

    ACCOUNT_NAME = "z"
    TYPE = ""
    POOL_VALUE = ""
    DELTA_VALUE =  0.1
    
    # Section of status variale
    new_ts = 0
    kline = {}
    flag = 0
    OPEN_LONG = {}
    OPEN_SHORT = {}
    OPEN_ORDER = {}
    FILLED_ORDER = {}

    # Param
    face = 100            # 合约面值
    add_times = 0         # 加仓次数初始化
    pos_state = 0         # 仓位状态初始化
    w1 = 20               # 开仓周期
    w2 = 10               # 平仓周期
    w3 = 20               # ATR周期
    a = 0.5               # 加仓阈值 价格涨跌0.5倍ATR加仓
    b = 2                 # 平仓阈值 价格涨跌2倍ATR止损
    c = 6                 # 止盈阈值
    d = 1                 # 盈利高点回撤1倍ATR则止盈
    max_add_times = 3     # 最大加仓次数
    risk_expo = 0.01      # 风险敞口

    while(1):     
        # request data
        # skip if ts is not updated.
        request_kline_data = get_contract_kline(self, symbol, period, size=150)
        for ts_data in request_kline_data:
            if ts_data["ts"] > new_ts:
                kline.add(ts_data)
                kline_updated = 1
        current_ts = request_kline_data[-1]["ts"]

        # compute signal
        if kline_updated:
            kline_updated = 0
            signal = DochianRange(kline)
        else:
            continue

        # get contract depth
        ret = get_contract_depth(self, symbol, "step0")
        buy_price = ret[]
        sell_price = ret[]

        # make decision and trade        
        """ 计算true range """
        true_range = max(kline.high.iloc[-1]-kline.low.iloc[-1],np.abs(kline.high.iloc[-1]-kline.close.iloc[-2]),np.abs(kline.low.iloc[-1]-kline.close.iloc[-2]))
        kline.loc[kline.index[-1],'TR'] = true_range   # 最新的TR
        atr = kline.TR.iloc[-w3:].mean()
        
        """ 判断交易信号 """
        
        isOpenLong = kline.close.iloc[-1] > kline.high.iloc[-w1-1:-1].max() and kline.close.iloc[-2] <= kline.high.iloc[-w1-2:-2].max()  # 做多信号
        isOpenShort = kline.close.iloc[-1] < kline.low.iloc[-w1-1:-1].min() and kline.close.iloc[-2] >= kline.low.iloc[-w1-2:-2].min()   # 做空信号
        isCloseLong = kline.close.iloc[-1] < kline.low.iloc[-w2-1:-1].min()    # 平掉多单（若有）
        isCloseShort = kline.close.iloc[-1] > kline.high.iloc[-w2-1:-1].max()  # 平掉空单（若有）
        
        """ 下单数量 """
        unit = account_asset*risk_expo*(kline.close.iloc[-1]**2)/face/atr      # 下单合约张数
        unit = int(max(unit,1))                        
        
        """ 判断如何下单 """
        if pos_state == 0:
            ## 无持仓
            if isOpenLong:
                ## 下多单
                order = give_order(self, amount=unit, price='', type_of_trade='对手价下多单')    # 对手价下单指令
                pos_state = 1
                basis_price = '成交价'         # 止盈止损基准价
                order_time = kline.index[-1]   # 下单时间
                
            elif isOpenShort:
                ## 下空单
                give_order(self, amount=unit, price='', type_of_trade='对手价下空单')   # 对手价下单指令
                pos_state = -1
                basis_price = '成交价'         # 止盈止损基准价
                order_time = kline.index[-1]   # 下单时间
        
        elif pos_state == 1:
            ## 持有多单
            max_price = kline.loc[order_time:,'close'].max()  # 持仓期间收盘价的最高价
            isAdd = kline.close.iloc[-1] >= basis_price + a*atr and add_times < max_add_times              # 价格上涨0.5倍ATR且加仓次数不超过3次则加仓
            isStopLoss = kline.close.iloc[-1] <= basis_price - b*atr                                       # 价格跌破2倍ATR则止损
            isStopProfit = max_price - basis_price >= c*atr and max_price - kline.close.iloc[-1] >= d*atr  # 价格涨破6倍ATR后跌落1倍ATR则及时止盈
            
            if (isCloseLong or isStopLoss or isStopProfit) and isOpenLong==0:
                # 正常出仓或者止损或者止盈（为保证平仓后不再同向开仓，需要此时不满足做多信号）
                if isOpenShort:
                    # 平多单的同时开空单
                    give_order(self, amount='全部已成交', price='', type_of_trade='对手价下平仓单')  # 将全部已成交委托平掉 
                    give_order(self, amount=unit, price='', type_of_trade='对手价下空单')           # 对手价下单做空
                    pos_state = -1
                    add_times = 0
                    basis_price = '成交价'         # 止盈止损基准价是该笔交易的成交价
                    order_time = kline.index[-1]   # 下单时间
                else:
                    # 只需要平仓
                    give_order(self, amount='全部已成交', price='', type_of_trade='对手价下平仓单')  
                    pos_state = 0
                    add_times = 0
                    
            elif isAdd:
                # 加仓
                give_order(self, amount=unit, price='', type_of_trade='对手价下多单')
                add_times +=1
                basis_price = '成交价'         # 止盈止损基准价更新为该笔交易的成交价
                order_time = kline.index[-1]   # 下单时间更新为现在
            else:
                continue
        
        else:
            ## 持有空单
            min_price = kline.loc[order_time:,'close'].min()  # 持仓期间收盘价的最低价
            isAdd = kline.close.iloc[-1] <= basis_price - a*atr and add_times < max_add_times              
            isStopLoss = kline.close.iloc[-1] >= basis_price + b*atr                                       
            isStopProfit = basis_price - min_price >= c*atr and kline.close.iloc[-1] - min_price >= d*atr 
            
            if (isCloseShort or isStopLoss or isStopProfit) and isOpenShort==0:
                # 正常出仓或者止损或者止盈（为保证平仓后不再同向开仓，需要此时不满足做空信号）
                if isOpenLong:
                    # 平空单的同时开多单
                    give_order(self, amount='全部已成交', price='', type_of_trade='对手价下平仓单')  # 将全部已成交委托平掉 
                    give_order(self, amount=unit, price='', type_of_trade='对手价下多单')           # 对手价下单做多
                    pos_state = 1
                    add_times = 0
                    basis_price = '成交价'         # 止盈止损基准价是该笔交易的成交价
                    order_time = kline.index[-1]   # 下单时间
                else:
                    # 只需要平仓
                    give_order(self, amount='全部已成交', price='', type_of_trade='对手价下平仓单')  
                    pos_state = 0
                    add_times = 0
                    
            elif isAdd:
                # 加仓
                give_order(self, amount=unit, price='', type_of_trade='对手价下空单')
                add_times +=1
                basis_price = '成交价'         # 止盈止损基准价更新为该笔交易的成交价
                order_time = kline.index[-1]   # 下单时间更新为现在
            else:
                continue


        # Update local status