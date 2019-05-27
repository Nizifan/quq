# -*- coding: utf-8 -*-
"""
Created on Wed May 22 10:48:27 2019

@author: shirley
"""

""" 
=========================================================================
**合约交割时间
合约最后一周的周五16:00（UTC+8）

**合约交割价格
系统以交割前最后一小时BTC等币种美元指数的算术平均值作为交割价格。

**合约交割规则
合约在到期时，会进行交割。系统采用价差交割（现金交割）方式。
系统会将到期未平仓合约，以交割价格进行平仓。
平仓产生的盈亏计入已实现盈亏。
交割会产生手续费，此手续费也会计入已实现盈亏。
合约在交割前最后10分钟，只能平仓，不能开仓。
=========================================================================

**合约品种
火币合约上线的品种为BTC合约、ETH合约、EOS合约、LTC合约、XRP合约、BCH合约、TRX合约。合约以美元USD计价，以对应的数字货币作为保证金，用户盈亏也以对应的数字货币进行结算。

**合约面值
所有合约交易，都以张为单位。每张合约，对应一定面值的数字货币。
BTC合约的面值为100美元，报价时的最小变动单位为0.01美元。
XRP合约的面值为10美元，报价时的最小变动单位为0.0001美元。
TRX合约的面值为10美元，报价时的最小变动单位为0.00001美元。
其他合约品种，如无特殊说明，其面值为10美元，报价时的最小变动单位为0.001美元。

**合约类型
火币合约提供三种合约类型，分别是：当周，次周，季度。
当周合约指在距离交易日最近的周五进行交割的合约；次周合约是指距离交易日最近的第二个周五进行交割的合约；季度合约是指交割日为3，6，9，12月中距离当前最近的一个月份的最后一个周五，且不与当周/次周合约的交割日重合。

正常情况下，每周五结算交割后，都会生成一个新的双周合约（当周合约和次周合约）。
在季度月的倒数第三个周五结算交割后，季度合约成为次周合约，因此系统生成新的季度合约。
=========================================================================
** 交易类型
买入开多（看涨）是指当用户对指数看多、看涨时，新买入一定数量的某种合约。进行“买入开多”操作，撮合成功后将增加多头仓位。
卖出平多（多单平仓）是指用户对未来指数行情不再看涨而补回的卖出合约，与当前持有的买入合约对冲抵消退出市场。进行“卖出平多”操作，撮合成功后将减少多头仓位。
卖出开空（看跌）是指当用户对指数看空、看跌时，新卖出一定数量的某种合约。进行“卖出开空”操作，撮合成功后将增加空头仓位。
买入平空（空单平仓）是指用户对未来指数行情不再看跌而补回的买入合约，与当前持有的卖出合约对冲抵消退出市场。进行“买入平空”操作，撮合成功后将减少空头仓位。
**在一个合约账户中，最多只能有6个仓位，即当周合约多仓、当周合约空仓、次周合约多仓、次周合约空仓、季度合约多仓、季度合约空仓。
=========================================================================
**下单方式
限价委托：用户需要自己指定下单的价格和数量。开仓和平仓都可以使用限价委托。
对手价下单：用户如果选择对手价下单，则用户只能输入下单数量，不能再输入下单价格。系统会在接收到此委托的一瞬间，读取当前最新的对手价格（如用户买入，则对手价为卖1价格；若为卖出，则对手价为买1价格），下达一个此对手价的限价委托。

"""

import warnings
warnings.filterwarnings("ignore")

import os
os.chdir("G:\BTC\python_huobi\REST_Python35_demo")
import pandas as pd
import numpy as np
import datetime,time,re
from dateutil.relativedelta import relativedelta

from HuobiDMService import HuobiDM
import TreatData as TD



print('>>>>>>>>>>>>>>>>>>>>>>账户设置>>>>>>>>>>>>>>>>>>>>>>')
url = 'https://api.hbdm.com'                       # 火币合约API链接
dm = HuobiDM(url, access_key, secrect_key)         # 创建账户实例



print('>>>>>>>>>>>>>>>>>>>>>>合约选择>>>>>>>>>>>>>>>>>>>>>>')
#### 合约选择（默认季度合约，季度合约存续期是3个月，节约换仓成本）
# 注：交割月份的倒数第三个周五16:00结算后会生成新的季度合约,因此在交割月份的最后一个周五前换仓，即平掉旧合约并在新合约上开相同仓位
symb = 'BTC'                                       # BTC ETF ---- BTC_CW, BTC_NW, BTC_CQ , ...  
type = 'quarter'
code = ''
map = {'quarter':'CQ','this_week':'CW','next_week':'NW'}  # 合约类型角标映射
contract_info = dm.get_contract_info(symbol=symb, contract_type=type, contract_code=code)
contract_info = contract_info['data'][0]           # 合约基本信息
code = contract_info['contract_code']              # 合约代码
face_val = contract_info['contract_size']          # 合约面值
min_move = contract_info['price_tick']             # 最小变动单位


print('>>>>>>>>>>>>>>>>>>>>>>转账>>>>>>>>>>>>>>>>>>>>>>')
## 法币交易购买USDT，币币交易购买BTC/USDT,BTC由币币账户转入合约账户
## 法币交易购买BTC,BTC由币币账户转入合约账户
initial_eqt = 0.1    # 初始转入0.1颗币


print('>>>>>>>>>>>>>>>>>>>>>>参数设置>>>>>>>>>>>>>>>>>>>>>>')
path = 'G:/BTC/python_huobi/REST_Python35_demo/'   # 数据保存路径
freq1 = '1min'      # 循环的频率
freq2 = '15min'     # 计算上轨的频率 1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1week, 1mon
w1 = 50             # 开仓参数（w1根K线，可改）
w2 = 5              # 平仓参数
w3 = 20             # ATR参数
sl = 1              # 止损参数
sp = [np.inf,np.inf]#止盈参数（默认不止盈）
add = 0.5           # 加仓参数
max_add_times = 2   # 最大加仓次数
lvg = 5             # 杠杆倍数
expo_ratio = 0.005  # 风险暴露比率
wait_time = 5       # 下单后等待成交的时间限制，超过5秒未成交则撤单并重下


print('>>>>>>>>>>>>>>>>>>>>>>预先抓取若干K线>>>>>>>>>>>>>>>>>>>>>>')
klines = dm.get_contract_kline(symbol=symb+'_'+map[type], period=freq2, size=100)
if klines['status'] == 'fail':
    print('爬虫程序不可用！！！！！！！！！！')
    input('')    # 等待输入以终止程序运行
    
klines = pd.DataFrame(klines['data'])
klines.index = [time.strftime("%Y-%m-%d %H:%M", time.localtime(d)) for d in klines.id]
klines['TR'] = TD.true_range(klines)             # 计算真实波幅
klines['ATR'] = klines.TR.rolling(w3).mean()     # 平均真实波幅

pnl = pd.DataFrame(index = klines.index ,columns=['合约张数','开仓价','平仓价','成本价','总权益','现金','保证金','未实现盈亏','已实现盈亏','手续费'])
pnl.loc[:,:] = 0
pnl.loc[:,['总权益','现金']] = initial_eqt


print('>>>>>>>>>>>>>>>>>>>>>>开始更新K线并交易>>>>>>>>>>>>>>>>>>>>>>')
add_times = 0
pos_state = 0
basis_price = 0
basis_time = 0
while 1:
    next_bartime = (datetime.datetime.strptime(klines[-1],'%Y-%m-%d %H:%M')+datetime.timedelta(seconds=60*int(re.sub(r'([\D]+)','',freq1)))).strftime("%Y-%m-%d %H:%M")  # 下一根K线的时间
    
    if datetime.datetime.now().strftime("%Y-%m-%d %H:%M") >= klines.index[-1] and datetime.datetime.now().strftime("%Y-%m-%d %H:%M") < next_bartime:
        #### 最近1根K线完成一套流程
        continue
    else:
        """ 
        ===============================
        新增K线和判断交易行为
        ===============================
        """ 
        
        #### 更新K线
        try_times = 0                                                         # 尝试次数
        while try_times < 10:
            kline = dm.get_contract_kline(symbol=symb+'_'+map[type], period=freq2, size=1)  # 抓取指定标的指定频率的近1根K线
            if kline['status'] == 'ok':
                # 抓取成功
                break
            else:
                # fail
                try_times += 1
        
        if kline['status'] == 'fail':
            print('抓取K线达到最大失败次数!!!!请检查原因\n'+'K线更新到: '+klines.index[-1])
            break
        
        kline = pd.DataFrame(kline['data'])
        kline.index = [time.strftime("%Y-%m-%d %H:%M", time.localtime(d)) for d in kline.id]  # 北京时间
        
        #### 计算ATR
        kline['TR'] = 0         # 初始化
        kline['ATR'] = 0        # 初始化
        klines = pd.concat([klines,kline], axis=0)
        klines.loc[klines.index[-1],'TR'] = max(klines.high.iloc[-1]-klines.low.iloc[-1],abs(klines.high.iloc[-1]-klines.close.iloc[-2]),abs(klines.low.iloc[-1]-klines.close.iloc[-2]))
        klines.loc[klines.index[-1],'ATR'] = klines.TR.iloc[-w3:].mean()
        pnl.loc[klines.index[-1]] = 0             # 初始化账户值
        
        
        #### 判断信号
        isOpenLong = klines.close.iloc[-1] > klines.high.iloc[-w1-1:-1].max() and klines.close.iloc[-2] <= klines.high.iloc[-w1-2:-2].max()
        isOpenShort = klines.close.iloc[-1] < klines.low.iloc[-w1-1:-1].min() and klines.close.iloc[-2] >= klines.low.iloc[-w1-2:-2].min()
        isCloseLong = klines.close.iloc[-1] < klines.low.iloc[-w2-1:-1].min()
        isCloseShort = klines.close.iloc[-1] > klines.high.iloc[-w2-1:-1].max()
        
        
        #### 海龟交易系统计算可开仓张数
        money = pnl.总权益.iloc[-1]*expo_ratio
        unit = money*(klines.close.iloc[-1]**2)/face_val/klines.ATR.iloc[-1]
        unit = np.round(max(unit,1))     # 合约张数取整


        #### 账户信息
        """
        try_times = 0                                                         # 尝试次数
        while try_times < 10:
            contract_info = dm.get_contract_account_info(symbol=symb)
            if contract_info['status'] == 'ok':
                break  # 请求成功
            else:
                try_times += 1
        
        if contract_info['status'] == 'error':
            print('抓取账户信息达到最大失败次数!!!!请检查原因\n'+'K线更新到: '+klines.index[-1])
            break
        """
        contract_info = dm.get_contract_account_info(symbol=symb)                                 # 指定品种的账户信息
        contract_info = contract_info['data'][0]
        max_unit = np.ceil(contract_info['margin_available']*lvg*klines.close.iloc[-1]/face_val)  # 最大开仓张数(在指定杠杆倍数下不能超过可用保证金)
        
        #### 设置下单参数
        if pos_state == 0:
            """ 当前无持仓 """
            unit = min(unit,max_unit)                        
            if (isOpenLong or isOpenShort) and unit <= 0:
                print('资金不足以开仓！！！！！')
                break
            
            if isOpenLong:
                pos_state = 1
                direction = 'buy'
                offset = 'open'
            elif isOpenShort:
                pos_state = -1
                direction = 'sell'
                offset = 'open'
            else:
                direction = ''
                offset = ''
        
        elif pos_state == 1:
            """ 当前持有多单 """
            isStopLoss = klines.close.iloc[-1] <= basis_price - sl*klines.ATR.iloc[-1]
            x = klines.loc[basis_time:,'close'].max()
            isStopProfit = x - basis_price >= sp[0]*klines.ATR.iloc[-1] and x - klines.close.iloc[-1] >= sp[1]*klines.ATR.iloc[-1]
            isAdd = klines.close.iloc[-1] >= basis_price + add*klines.ATR.iloc[-1] and add_times < max_add_times
            
            if (isStopLoss or isStopProfit or isCloseLong) and isOpenLong==0:
                if isOpenShort == 0:
                    # 平多单
                    pos_state = 0
                    direction = 'sell'
                    offset = 'close'
                else:
                    # 平多+开空 -- 批量下单
                    pos_state = -1
                    
                    
            
            
        ## 对手价下单(默认不上传客户ID和价格)
        order_volume = unit-0            # 下单数量初始化
        trade_volume = 0                 # 已成交数量初始化
        order_split = []
        while trade_volume < unit:          
            # 下单或追单--只要已成交数量未达到设置
            order_send = dm.send_contract_order(symbol=symb,contract_type=type,contract_code=code,client_order_id='',\
                                                price='',volume=order_volume,direction=direction,offset=offset,lever_rate=lvg,order_price_type='opponent')
            order_id = order_send['data']['order_id']                              # 订单ID
            order_time = time.time()                                               # 当前时间
            while time.time() - order_time <= wait_time:
                order_info = dm.get_contract_order_info(symb,order_id=order_id)    # 订单信息
                if order_info['data'][0]['trade_volume'] == order_info['data'][0]['volume']:
                    # 全部成交
                    break
                else:
                    # 未全部成交
                    continue
                
            if order_info['data'][0]['trade_volume'] == order_info['data'][0]['volume']:
                # 规定时间内全部成交
                order_split.append([order_info['data'][0]['trade_volume'],order_info['data'][0]['trade_avg_price'],order_info['data'][0]['fee']])
                break
            else:
                # 规定时间内未全部成交--撤单
                order_cancel = dm.cancel_contract_order(symb, order_id=order_id, client_order_id='')
                order_volume = order_info['data'][0]['volume'] - order_info['data'][0]['trade_volume']
                if order_info['data'][0]['trade_volume'] > 0:
                    # 已成交数量大于0
                    order_split.append([order_info['data'][0]['trade_volume'],order_info['data'][0]['trade_avg_price'],order_info['data'][0]['fee']])
                    
                
        ## 计算本次建仓的持仓均价
        order_split = np.array(order_split)
        basis_price = order_split[:,0].sum()/(order_split[:,0]/order_split[:,1]).sum()
        basis_time = klines.index[-1]
        
        pos_info = dm.get_contract_position_info(symbol=symb)      # 指定品种的持仓信息
        pos_info = pos_info['data']

        pnl.loc[klines.index[-1],'合约张数'] = pnl.loc[klines.index[-1],'合约张数']+order_split[:,0].sum()
        pnl.loc[klines.index[-1],'开仓价'] = basis_price
        pnl.loc[klines.index[-1],'手续费'] = order_split[:,2].sum()

                        

                
                

        
        
        
    
    
    
    
    

