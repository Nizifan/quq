# -*- coding: utf-8 -*-
"""
Created on Tue May 28 15:40:27 2019

@author: shirley
"""

# -*- coding: utf-8 -*-
"""
Created on Tue May 14 16:28:09 2019
@author: shirley
"""

import warnings
warnings.filterwarnings("ignore")

import os
os.chdir("G:\BTC\python_huobi\REST_Python35_demo\github_files")
import pandas as pd
import numpy as np
import datetime,time,re
from dateutil.relativedelta import relativedelta

from HuobiDMService import HuobiDM
import TreatData as TD




def send_order(dm,symbol,contract_type,contract_code,volume,direction,offset,client_order_id='',price='',lever_rate=5,order_price_type='opponent',wait_num=5):
    """下单+撤单+追单 直到全部成交
    dm : 已创建的账户
    默认5倍杠杆、对手价下单、最多查询5次
    """
    
    FILLED_ORDER = []  # 保存每笔交易详情:order_id 成交量 成交均价
    ret = dm.send_contract_order(symbol=symbol,contract_type=contract_type,contract_code=contract_code,client_order_id=client_order_id,\
                                 price=price,volume=volume,direction=direction,offset=offset,lever_rate=lever_rate,order_price_type=order_price_type)
    order_id = ret["data"]["order_id"]
    wait_count = wait_num
    
    while 1:
        time.sleep(0.2)
        order_info = dm.get_contract_order_info(symbol,order_id=order_id)    # 订单信息
        
        if order_info["data"][0]["volume"] == order_info["data"][0]["trade_volume"]:
            # 全部成交
            FILLED_ORDER.append({name:order_info['data'][0][name] for name in ['order_id','trade_volume','trade_avg_price']})
            return pd.DataFrame(FILLED_ORDER)
        
        else:
            if wait_count > 0:
                wait_count -= 1
                continue
            else:
                # 查询次数达到上限仍然没有成交完 
                while 1:
                    order_cancel = dm.cancel_contract_order(symbol, order_id=order_id)             # 撤单:(1)撤单成功==>已成交数量不会再变&存在部分未成交 ; (2)撤单失败==>之后可能会继续成交
                    order_info = dm.get_contract_order_info(symbol, order_id=order_id)             # 订单信息
                    unit = order_info['data'][0]['volume'] - order_info['data'][0]['trade_volume'] # 未成交委托
                    
                    if order_info['data'][0]['status'] == 6 or unit == 0:
                        # 全部成交==>撤单失败
                        FILLED_ORDER.append({name:order_info['data'][0][name] for name in ['order_id','trade_volume','trade_avg_price']})
                        return pd.DataFrame(FILLED_ORDER)
                    
                    elif order_id in order_cancel['data']['success']:
                        # 撤单成功==>存在部分未成交,未成交部分不再改变
                        FILLED_ORDER.append({name:order_info['data'][0][name] for name in ['order_id','trade_volume','trade_avg_price']})
                        # 追单
                        ret = dm.send_contract_order(symbol=symbol,contract_type=contract_type,contract_code=contract_code,client_order_id=client_order_id,\
                                                     price=price,volume=unit,direction=direction,offset=offset,lever_rate=lever_rate,order_price_type=order_price_type)
                        order_id = ret["data"]["order_id"]
                        wait_count = wait_num
                        break
                    
                    else:
                        # 未全部成交下的撤单失败--重新撤单
                        time.sleep(0.2)
                    
                    """
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
                    """


def write_log(log_file, string, ts):
    log_file.write(string(time.time()) + ":ts" + ts + ":string")



def main(dm,symbol,contract_type,params,initial_eqt=0.1,lvg=5,wait_num=5,freq='15min'):
    """ 换仓日16:00前关掉自动交易，若持有合约则强平,16:00后重新开始新合约的自动交易
    =========================================
    dm : 账户
    contract_info : 合约
    params : 策略参数
    initial_eqt : 初始资金(默认0.1颗币)
    lvg : 杠杆倍数 1/5/10/20
    wait_num : 查询次数上限
    =========================================
    """
    
    ## 策略参数
    w1 = params['w1']                              # 开仓参数: 价格超过前w1根K线的最高价或低于最低价
    w2 = params['w2']                              # 平仓参数: 价格低于前w2根K线的最低价就平掉多单
    w3 = params['w3']                              # ATR参数: 前20根K线的TR的均值
    stop_loss = params['stop_loss']                # 止损参数: 价格跌破1倍ATR就止损
    big_float = params['big_float']                # 止盈参数
    draw_back = params['draw_back']                # 盈利高点回撤参数
    add = params['add']                            # 加仓参数
    max_add_times = params['max_add_times']        # 最大加仓次数
    risk_ratio = params['risk_ratio']              # 风险暴露比率
    
    ## 合约参数
    # 2019.6.14(交割月倒数第3个周五)16:00结算后,BTC190628合约会成为次周合约,且产生新的季度合约
    # 20190614 16:00前的季度合约是BTC190628 之后的季度合约是BTC190927
    # 换仓: 20190614 16:00之后，BTC190628若有仓位则平仓且在BTC190927上开相同数量
    contract_info = dm.get_contract_info(symbol=symbol, contract_type=contract_type, contract_code='')
    contract_info = contract_info['data'][0]                  # 当前的季度合约的合约信息
    face_val = contract_info['contract_size']                 # 面值 100
    min_move = contract_info['price_tick']                    # 最小变动单位0.01
    
    contract_code = contract_info['contract_code']            # 20190614 16:00前：BTC190628
    delivery_date = contract_info['delivery_date']            # 交割日
    # 换仓日：当前日期一定在换仓日16:00之前
    chgpos_date = (datetime.datetime.strptime(delivery_date,'%Y%m%d')+datetime.timedelta(days=-14)).strftime("%Y%m%d") 
    
    map = {'quarter':'CQ','this_week':'CW','next_week':'NW'}  # 合约类型角标映射
    contract_name = symbol+'_'+map[contract_type]             # BTC_CQ
    
    """
    symbol = contract_info['symbol']               # BTC
    contract_type = contract_info['contract_type'] # quarter
    """

    ## 预抓K线
    klines = dm.get_contract_kline(symbol=contract_name, period=freq, size=200)             
    klines = pd.DataFrame(klines['data'])
    klines.index = [time.strftime("%Y-%m-%d %H:%M", time.localtime(d)) for d in klines.id]  # 北京时间
    klines['TR'] = TD.true_range(klines)             # 计算真实波幅
    klines['ATR'] = klines.TR.rolling(w3).mean()     # 平均真实波幅

    ## 持仓信息初始化
    pnl = pd.DataFrame(index = klines.index ,columns=['合约张数','开仓价','平仓价'])          # 合约张数有正负,表示多/空
    pnl.loc[:,:] = 0
    
    pos_state = 0    # 仓位状态初始化
    add_times = 0    # 加仓次数初始化
    basis_price = 0  # 止盈止损加仓基准价--上一次开仓价格
    basis_time = 0   # 止盈止损加仓的参考时间--上一次开仓的时间
    
    while datetime.datetime.now().strftime("%Y%m%d %H:%M") < chgpos_date+' 15:58': 
        """ 当前日期没到换仓日 """
        
        # 更新K线:只更新走完的K线
        kline = dm.get_contract_kline(symbol=contract_name, period=freq, size=20)
        kline = pd.DataFrame(kline['data'])
        kline.index = [time.strftime("%Y-%m-%d %H:%M", time.localtime(d)) for d in kline.id]  # 北京时间
        num = (kline.index>klines.index[-1]).sum()  # K线更新数量

        if num == 0:
            # 没有更新K线
            continue
        else:
            print('K线更新到：'+kline.index[-1])
            # K线有更新且最新的K线已经走完
            klines = pd.concat([klines,kline[kline.index>klines.index[-1]]], axis=0)
        
        # 更新TR和ATR
        klines.loc[klines.index[-num:],'TR'] = np.maximum(klines.high.values[-num:]-klines.low.values[-num:],abs(klines.high.values[-num:]-klines.close.values[-num-1:-1]),abs(klines.low.values[-num:]-klines.close.values[-num-1:-1]))
        klines.loc[klines.index[-num:],'ATR'] = klines.TR.iloc[-w3-num+1:].rolling(w3).mean().values[-num:]
        
        # 最新一根K线的交易信号(正常情况每次最多更新1根K线,若中断交易导致缺失多根K线,则只能对最近1根K线做交易，忽略中间的K线)
        pnl.loc[klines.index[-1]] = 0  # 只更新最新一根K线的持仓
        
        # 换仓日16:00结算，因此15:00后不再开仓
        isOpenLong = datetime.datetime.now().strftime("%Y%m%d %H:%M") < chgpos_date+' 15:00' and klines.close.iloc[-1] > klines.high.iloc[-w1-1:-1].max() and klines.close.iloc[-2] <= klines.high.iloc[-w1-2:-2].max()
        isOpenShort = datetime.datetime.now().strftime("%Y%m%d %H:%M") < chgpos_date+' 15:00' and klines.close.iloc[-1] < klines.low.iloc[-w1-1:-1].min() and klines.close.iloc[-2] >= klines.low.iloc[-w1-2:-2].min()
        isCloseLong = klines.close.iloc[-1] < klines.low.iloc[-w2-1:-1].min()
        isCloseShort = klines.close.iloc[-1] > klines.high.iloc[-w2-1:-1].max()
        
        # 账户信息
        account_info = dm.get_contract_account_info(symbol=symbol) 
        account_info = account_info['data'][0]   # 账户信息
        asset = account_info['margin_balance']   # 账户权益 = 账户余额+已实现未结算盈亏+未实现盈亏
        max_unit = np.ceil(account_info['margin_available']*lvg*klines.close.iloc[-1]/face_val) # 现有可用保证金在给定杠杆下的最大开仓数量
        
        unit = asset*risk_ratio*(klines.close.iloc[-1]**2)/face_val/klines.ATR.iloc[-1]
        unit = np.round(max(unit,1))             # 海龟交易法则计算开仓数量(至少做1张合约)
        
        """ 持仓信息
        position_info = dm.get_contract_position_info(symbol=symbol)['data']
        """
        
        offset = ''   # 下单参数初始化
        if pos_state == 1:
            isStopLoss = klines.close.iloc[-1] <= basis_price - stop_loss*klines.ATR.iloc[-1] # 是否止损
            x = klines.loc[basis_time:,'close'].max()   # 上次开仓以来的最高价
            isStopProfit = x - basis_price >= big_float*klines.ATR.iloc[-1] and x - klines.close.iloc[-1] >= draw_back*klines.ATR.iloc[-1] # 是否止盈--盈利高点回撤
            isAdd = klines.close.iloc[-1] >= basis_price + add*klines.ATR.iloc[-1] and add_times < max_add_times # 是否加仓
            
            if (isStopLoss or isStopProfit or isCloseLong) and isOpenLong==0:
                # 全部平仓
                pos_state = 0
                direction = 'sell'
                offset = 'close'
                volume = np.abs(pnl.合约张数.iloc[-2])  # 可平仓数量：position_info[0]['available']
                add_times = 0
            elif isAdd and max_unit>0:
                # 加仓
                add_times += 1
                basis_time = klines.index[-1]
                volume = min(unit,max_unit)
                direction = 'buy'
                offset = 'open'
            else:
                pnl.loc[klines.index[-1],'合约张数'] = pnl.合约张数.iloc[-2]  # 仓位不变
                continue
        
        if pos_state == -1:
            isStopLoss = klines.close.iloc[-1] >= basis_price + stop_loss*klines.ATR.iloc[-1] # 是否止损
            x = klines.loc[basis_time:,'close'].min()   # 上次开仓以来的最低价
            isStopProfit = basis_price-x >= big_float*klines.ATR.iloc[-1] and klines.close.iloc[-1]-x >= draw_back*klines.ATR.iloc[-1] # 是否止盈--盈利高点回撤
            isAdd = klines.close.iloc[-1] <= basis_price - add*klines.ATR.iloc[-1] and add_times < max_add_times # 是否加仓
            
            if (isStopLoss or isStopProfit or isCloseShort) and isOpenShort==0:
                # 全部平仓
                pos_state = 0
                direction = 'buy'
                offset = 'close'
                volume = np.abs(pnl.合约张数.iloc[-2])  # 可平仓数量：position_info[0]['available']
                add_times = 0
            elif isAdd and max_unit>0:
                # 加仓
                add_times += 1
                basis_time = klines.index[-1]
                volume = min(unit,max_unit)
                direction = 'sell'
                offset = 'open'
            else:
                pnl.loc[klines.index[-1],'合约张数'] = pnl.合约张数.iloc[-2]  # 仓位不变
                continue
        
        if offset != '':
            # 下单
            order_split = send_order(dm,symbol,contract_type,contract_code,volume,direction,offset,client_order_id='',price='',lever_rate=lvg,order_price_type='opponent',wait_num=wait_num)
            trade_price = order_split.trade_volume.sum()/(order_split.trade_volume/order_split.trade_avg_price).sum() # 成交均价
            if offset == 'open':
                # 加仓==>加仓完成后直接进入下一次循环
                pnl.loc[klines.index[-1],'合约张数'] = pnl.合约张数.iloc[-2] + pos_state*order_split.trade_volume.sum()
                pnl.loc[klines.index[-1],'开仓价'] = trade_price
                basis_price = trade_price
                continue
            else:
                # 平仓==>平仓后可能立即反向开仓
                pnl.loc[klines.index[-1],'平仓价'] = trade_price
            
            # 平仓后更新账户信息
            account_info = dm.get_contract_account_info(symbol=symbol) 
            account_info = account_info['data'][0]   # 账户信息
            asset = account_info['margin_balance']   # 账户权益 = 账户余额+已实现未结算盈亏+未实现盈亏
            max_unit = np.ceil(account_info['margin_available']*lvg*klines.close.iloc[-1]/face_val) # 现有可用保证金在给定杠杆下的最大开仓数量
            
            unit = asset*risk_ratio*(klines.close.iloc[-1]**2)/face_val/klines.ATR.iloc[-1]
            unit = np.round(max(unit,1))             # 海龟交易法则计算开仓数量(至少做1张合约)
        
        """
        ====================================
        # 没有持仓的状态下会进入以下程序
        ====================================
        """
        if (isOpenLong or isOpenShort) and max_unit <= 0:
            print('空仓状态下资金不足以开仓!!!!!!!')
            break
        
        if isOpenLong:
            # 做多
            pos_state = 1
            basis_time = klines.index[-1]
            volume = min(unit,max_unit)
            direction = 'buy'
            offset = 'open'
        elif isOpenShort:
            # 做空
            pos_state = -1
            basis_time = klines.index[-1]
            volume = min(unit,max_unit)
            direction = 'sell'
            offset = 'open'
        else:
            # 无信号--跳过
            continue
        
        # 下单--只有建仓单
        order_split = send_order(dm,symbol,contract_type,contract_code,volume,direction,offset,client_order_id='',price='',lever_rate=lvg,order_price_type='opponent',wait_num=wait_num)
        trade_price = order_split.trade_volume.sum()/(order_split.trade_volume/order_split.trade_avg_price).sum() # 成交均价
        pnl.loc[klines.index[-1],'合约张数'] = pos_state*order_split.trade_volume.sum()  # 合约数量有正负，表示多或空
        pnl.loc[klines.index[-1],'开仓价'] = trade_price
        basis_price = trade_price
            
        time.sleep(0.1)
    
    """ 超过换仓日下午3点 """
    if pnl.合约张数.iloc[-1] != 0:
        # 还有合约--强制平仓
        volume = np.abs(pnl.合约张数.iloc[-1])
        direction = 'buy' if pnl.合约张数.iloc[-1] < 0 else 'sell'
        offset = 'close'
        
        order_split = send_order(dm,'','',contract_code,volume,direction,offset,client_order_id='',price='',lever_rate=lvg,order_price_type='opponent',wait_num=wait_num)
        trade_price = order_split.trade_volume.sum()/(order_split.trade_volume/order_split.trade_avg_price).sum() # 成交均价
        pnl.loc['close'] = [0,0,trade_price]
        
    return contract_code,pnl
       

            
            
print('>>>>>>>>>>>>>>>>>>>>>>账户设置>>>>>>>>>>>>>>>>>>>>>>')
url = 'https://api.hbdm.com'                       # 火币合约API链接
access_key = ''
secrect_key = ''
dm = HuobiDM(url, access_key, secrect_key)         # 创建账户实例


print('>>>>>>>>>>>>>>>>>>>>>>合约选择>>>>>>>>>>>>>>>>>>>>>>')
#### 合约选择（默认季度合约，季度合约存续期是3个月，节约换仓成本）
# 注：交割月份的倒数第三个周五16:00结算后会生成新的季度合约,因此在交割月份的最后一个周五前换仓，即平掉旧合约并在新合约上开相同仓位
symb = 'BTC'                                       # BTC ETF ---- BTC_CW, BTC_NW, BTC_CQ , ...  
type = 'quarter'


print('>>>>>>>>>>>>>>>>>>>>>>转账>>>>>>>>>>>>>>>>>>>>>>')
## 法币交易购买USDT，币币交易购买BTC/USDT,BTC由币币账户转入合约账户
## 法币交易购买BTC,BTC由币币账户转入合约账户
initial_eqt = 0.1    # 初始转入0.1颗币


print('>>>>>>>>>>>>>>>>>>>>>>参数设置>>>>>>>>>>>>>>>>>>>>>>')
path = 'G:/BTC/python_huobi/REST_Python35_demo/github_files/'   # 数据保存路径
params = {'w1':50,'w2':5,'w3':20,'stop_loss':1,'big_float':np.inf,'draw_back':np.inf,'add':0.5,'max_add_times':2,'risk_ratio':0.005}
lvg = 5
wait_num = 5
freq = '15min'


print('>>>>>>>>>>>>>>>>>>>>>>开始交易>>>>>>>>>>>>>>>>>>>>>>')
contract_codes = []
pnls = []
contract_code,pnl = main(dm,symb,type,params,initial_eqt=initial_eqt,lvg=lvg,wait_num=wait_num,freq=freq)
contract_codes.append(contract_code)
pnls.append(pnl)
while 1:
    """ 两次循环间隔1个季度 """
    account_info = dm.get_contract_account_info(symbol=symb)  # 账户信息
    account_info = account_info['data'][0]
    asset = account_info['margin_balance']                    # 账户权益
    contract_code,pnl = main(dm,symb,type,params,initial_eqt=asset,lvg=lvg,wait_num=wait_num,freq=freq)
