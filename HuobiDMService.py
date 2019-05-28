#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 20180917
# @Author  : zhaobo
# @github  : 

from HuobiDMUtil import http_get_request, api_key_post

import smtplib  #加载smtplib模块
from email.mime.text import MIMEText
from email.utils import formataddr


class HuobiDM:

    def __init__(self,url,access_key,secret_key):
        self.__url = url
        self.__access_key = access_key
        self.__secret_key = secret_key

    
    '''
    ======================
    Market data API
    ======================
    '''

    def send_mail(self,error_message, mail_to):
        my_sender = '发件人邮箱账号' #发件人邮箱账号，为了后面易于维护，所以写成了变量
        my_user = ''
        ret=True
        try:
            msg=MIMEText('填写邮件内容','plain','utf-8')
            msg['From']=formataddr(["发件人邮箱昵称",my_sender])   #括号里的对应发件人邮箱昵称、发件人邮箱账号
            msg['To']=formataddr(["收件人邮箱昵称",my_user])   #括号里的对应收件人邮箱昵称、收件人邮箱账号
            msg['Subject']="Network Exception is hit" #邮件的主题，也可以说是标题

            server=smtplib.SMTP("smtp.xxx.com",25)  #发件人邮箱中的SMTP服务器，端口是25
            server.login(my_sender,"发件人邮箱密码")    #括号中对应的是发件人邮箱账号、邮箱密码
            server.sendmail(my_sender,[my_user,],msg.as_string())   #括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.quit()   #这句是关闭连接的意思
        except Exception:   #如果try中的语句没有执行，则会执行下面的ret=False
            ret=False
        return ret


    def send_alert(self,error_message):
        self.send_mail(error_message, "505529920@qq.com")
        self.send_mail(error_message, "2691266020@qq.com")
    
    
    def http_get_request_with_retry(self, url, param):
        retry_count = 3
        while retry_count > 0:
            ret = http_get_request(url, param)
            if ret["status"] == "fail":
                retry_count -= 1
            else:
                return ret
        self.TODOSendAlert()
                

    # 获取合约信息
    def get_contract_info(self, symbol='', contract_type='', contract_code=''):
        """
        参数名称         参数类型  必填    描述
        symbol          string  false   "BTC","ETH"...
        contract_type   string  false   合约类型: this_week:当周 next_week:下周 quarter:季度
        contract_code   string  false   BTC181228
        备注：如果contract_code填了值，那就按照contract_code去查询，如果contract_code 没有填值，则按照symbol+contract_type去查询
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        if contract_type:
            params['contract_type'] = contract_type
        if contract_code:
            params['contract_code'] = contract_code
    
        url = self.__url + '/api/v1/contract_contract_info'
        return self.http_get_request_with_retry(url, params)
    
    
    # 获取合约指数信息
    def get_contract_index(self, symbol):
        """
        :symbol    "BTC","ETH"...
        """
        params = {'symbol': symbol}
    
        url = self.__url + '/api/v1/contract_index'
        return self.http_get_request_with_retry(url, params)
    
    
    # 获取合约最高限价和最低限价
    def get_contract_price_limit(self, symbol='', contract_type='', contract_code=''):
        """
        :symbol          "BTC","ETH"...
        :contract_type   合约类型: this_week:当周 next_week:下周 quarter:季度
        "contract_code   BTC180928
        备注：如果contract_code填了值，那就按照contract_code去查询，如果contract_code 没有填值，则按照symbol+contract_type去查询
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        if contract_type:
            params['contract_type'] = contract_type
        if contract_code:
            params['contract_code'] = contract_code
    
        url = self.__url + '/api/v1/contract_price_limit'
        return self.http_get_request_with_retry(url, params)
    
    
    # 获取当前可用合约总持仓量
    def get_contract_open_interest(self, symbol='', contract_type='', contract_code=''):
        """
        :symbol          "BTC","ETH"...
        :contract_type   合约类型: this_week:当周 next_week:下周 quarter:季度
        "contract_code   BTC180928
        备注：如果contract_code填了值，那就按照contract_code去查询，如果contract_code 没有填值，则按照symbol+contract_type去查询
        """
        params = {'symbol': symbol,
                  'contract_type': contract_type,
                  'contract_code': contract_code}
    
        url = self.__url + '/api/v1/contract_open_interest'
        return self.http_get_request_with_retry(url, params)   
        
    
    # 获取行情深度
    def get_contract_depth(self, symbol, type):
        """
        :param symbol:   BTC_CW, BTC_NW, BTC_CQ , ...
        :param type: 可选值：{ step0, step1, step2, step3, step4, step5 （合并深度0-5）；step0时，不合并深度 }
        :return:
        """
        params = {'symbol': symbol,
                  'type': type}
    
        url = self.__url + '/market/depth'
        return self.http_get_request_with_retry(url, params)
    
    
    # 获取KLine
    def get_contract_kline(self, symbol, period, size=150):
        """
        :param symbol  BTC_CW, BTC_NW, BTC_CQ , ...
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1week, 1mon }
        :param size: [1,2000]
        :return:
        """
        params = {'symbol': symbol,
                  'period': period}
        if size:
            params['size'] = size
    
        url = self.__url + '/market/history/kline'
        return self.http_get_request_with_retry(url, params)
    
    
    # 获取聚合行情
    def get_contract_market_merged(self, symbol):
        """
        :symbol	    "BTC_CW","BTC_NW", "BTC_CQ" ...
        """
        params = {'symbol': symbol}
    
        url = self.__url + '/market/detail/merged'
        return self.http_get_request_with_retry(url, params)
    
    
    # 获取市场最近成交记录
    def get_contract_trade(self, symbol, size=1):
        """
        :param symbol: 可选值：{ BTC_CW, BTC_NW, BTC_CQ, etc. }
        :return:
        """
        params = {'symbol': symbol,
                  'size' : size}
    
        url = self.__url + '/market/trade'
        return self.http_get_request_with_retry(url, params)
    
    
    # 批量获取最近的交易记录
    def get_contract_batch_trade(self, symbol, size=1):
        """
        :param symbol: 可选值：{ BTC_CW, BTC_NW, BTC_CQ, etc. }, size: int
        :return:
        """
        params = {'symbol': symbol,
                  'size' : size}
    
        url = self.__url + '/market/history/trade'
        return self.http_get_request_with_retry(url, params)
    
    

    '''
    ==============================================
    Account API
    ==============================================
    '''
    
    # 获取用户账户信息
    def get_contract_account_info(self, symbol=''):
        """
        :param:
            symbol: "BTC","ETH"...如果缺省，默认返回所有品种
        :return: 
            status : 'ok' 'error'
            data:[{
                symbol:品种代码
                margin_balance : 账户权益
                margin_position : 持仓保证金（当前持有仓位所占用的保证金）
                margin_frozen : 冻结保证金
                margin_available : 可用保证金
                risk_rate : 保证金率
                liquidation_price : 预估强平价
                withdraw_available : 可划转数量
                profit_real : 已实现盈亏(以平仓且未结算的盈亏)--从上一个交割结算时间开始计的平仓盈亏(交割结算后计入账户余额)--结算前可作为保证金但不能提现--已实现盈亏在结算前计入可用保证金
                profit_unreal : 未实现盈亏 -- 当前未平仓位的盈亏
                }]
        """
        
        params = {}
        if symbol:
            params["symbol"] = symbol
    
        request_path = '/api/v1/contract_account_info'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    # 获取用户持仓信息
    def get_contract_position_info(self, symbol=''):
        """
        :param:
            symbol: "BTC","ETH"...如果缺省，默认返回所有品种
        :return:
            status : 'ok' 'error'
            data:
                [{
                symbol ： BTC
                contract_code : BTC180914
                contract_type : quarter
                volume : 持仓量
                available : 可平仓数量
                frozen : 冻结数量
                cost_open : 开仓均价
                cost_hold : 持仓均价
                profit_unreal : 未实现盈亏
                profit_rate : 收益率
                profit : 收益
                position_margin : 持仓保证金
                lever_rate : 杠杆倍数
                direction : 'buy' 'sell'
                ts : 时间
                }]
        """
        
        params = {}
        if symbol:
            params["symbol"] = symbol
    
        request_path = '/api/v1/contract_position_info'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    
    '''
    ==============================================
    Trade API
    ==============================================
    '''
    #### 合约下单
    def send_contract_order(self, symbol, contract_type, contract_code, 
                            client_order_id, price,volume,direction,offset,
                            lever_rate,order_price_type):
        """
        params:
        :symbol: "BTC","ETH"..
        :contract_type: "this_week", "next_week", "quarter"
        :contract_code: "BTC181228"
        :client_order_id: 客户自己填写和维护，这次一定要大于上一次(可不填) 格式-long 
        :price             必填   价格 格式-decimal
        :volume            必填  委托数量（张） 格式-long
        :direction         必填  "buy" "sell"
        :offset            必填   "open"开, "close"平
        :lever_rate        必填  杠杆倍数 格式-int
        :order_price_type  必填   "limit"限价， "opponent" 对手价
        **备注：如果contract_code填了值，那就按照contract_code去下单，如果contract_code没有填值，则按照symbol+contract_type去下单。
        **对手价下单price价格参数不用传，对手价下单价格是买一和卖一价。
        
        开平方向：
        开多：买入开多(direction用buy、offset用open)
        平多：卖出平多(direction用sell、offset用close)
        开空：卖出开空(direction用sell、offset用open)
        平空：买入平空(direction用buy、offset用close)
        
        return:
            status : 'ok' 'error'
            data : 
                {order_id : 订单ID, client_order_id : 用户下单时填写的客户端订单ID，没填则不返回}
            ts
        """
        
        params = {"price": price,
                  "volume": volume,
                  "direction": direction,
                  "offset": offset,
                  "lever_rate": lever_rate,
                  "order_price_type": order_price_type}
        if symbol:
            params["symbol"] = symbol
        if contract_type:
            params['contract_type'] = contract_type
        if contract_code:
            params['contract_code'] = contract_code
        if client_order_id:
            params['client_order_id'] = client_order_id
    
        request_path = '/api/v1/contract_order'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    
    # 合约批量下单
    def send_contract_batchorder(self, orders_data):
        """
        orders_data: example:
        orders_data = {'orders_data': [
               {'symbol': 'BTC', 'contract_type': 'quarter',  
                'contract_code':'BTC181228',  'client_order_id':'', 
                'price':1, 'volume':1, 'direction':'buy', 'offset':'open', 
                'leverRate':20, 'orderPriceType':'limit'},
               {'symbol': 'BTC','contract_type': 'quarter', 
                'contract_code':'BTC181228', 'client_order_id':'', 
                'price':2, 'volume':2, 'direction':'buy', 'offset':'open', 
                'leverRate':20, 'orderPriceType':'limit'}]}    
            
        Parameters of each order: refer to send_contract_order
        """
        
        params = orders_data
        request_path = '/api/v1/contract_batchorder'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    # 撤销订单
    def cancel_contract_order(self, symbol, order_id='', client_order_id=''):
        """
        参数名称          是否必须 类型     描述
        symbol           true   string  BTC, ETH, ...
        order_id	         false  string  订单ID（ 多个订单ID中间以","分隔,一次最多允许撤消50个订单 ）
        client_order_id  false  string  客户订单ID(多个订单ID中间以","分隔,一次最多允许撤消50个订单)
        备注： order_id 和 client_order_id都可以用来撤单，同时只可以设置其中一种，如果设置了两种，默认以order_id来撤单。
        """
        
        params = {"symbol": symbol}
        if order_id:
            params["order_id"] = order_id
        if client_order_id:
            params["client_order_id"] = client_order_id  
    
        request_path = '/api/v1/contract_cancel'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    # 全部撤单
    def cancel_all_contract_order(self, symbol):
        """
        symbol: BTC, ETH, ...
        """
        
        params = {"symbol": symbol}
    
        request_path = '/api/v1/contract_cancelall'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    """
    ==================================================================
    订单信息
    ==================================================================
    """
    # 获取合约订单信息
    def get_contract_order_info(self, symbol, order_id='', client_order_id=''):
        """
        参数名称	        是否必须	类型	    描述
        symbol           true    string  BTC, ETH, ...
        order_id	        false	string	订单ID（ 多个订单ID中间以","分隔,一次最多允许查询20个订单 ）
        client_order_id	 false	string	客户订单ID(多个订单ID中间以","分隔,一次最多允许查询20个订单)
        
        备注：order_id和client_order_id都可以用来查询，同时只可以设置其中一种，如果设置了两种，默认以order_id来查询。
        周五交割结算后，会把结束状态的订单（5部分成交已撤单 6全部成交 7已撤单）删除掉。
        
        return:
        data:[{
            symbol
            contract_type
            contract_code
            volume : 委托数量
            price : 委托数量
            order_price_type : 'limit' 'opponent'
            direction : "buy":买 "sell":卖
            offset : "open":开 "close":平
            lever_rate : 杠杆倍数	1\5\10\20
            order_id : 订单ID
            client_order_id	: 客户订单ID
            trade_volume : 成交数量   trade_avg_price:成交均价   fee:手续费
            
        """
        
        params = {"symbol": symbol}
        if order_id:
            params["order_id"] = order_id
        if client_order_id:
            params["client_order_id"] = client_order_id  
    
        request_path = '/api/v1/contract_order_info'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    # 获取合约订单明细信息
    def get_contract_order_detail(self, symbol, order_id, order_type, created_at, page_index=None, page_size=None):
        """
        参数名称     是否必须  类型    描述
        symbol      true	    string "BTC","ETH"...
        order_id    true	    long	   订单id
        order_type  true    int    订单类型。1:报单， 2:撤单， 3:爆仓， 4:交割
        created_at  true    number 订单创建时间
        page_index  false   int    第几页,不填第一页
        page_size   false   int    不填默认20，不得多于50
        """
        
        params = {"symbol": symbol,
                  "order_id": order_id,
                  "order_type": order_type,
                  "created_at": created_at}
        if page_index:
            params["page_index"] = page_index
        if page_size:
            params["page_size"] = page_size  
    
        request_path = '/api/v1/contract_order_detail'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    # 获取合约当前未成交委托
    def get_contract_open_orders(self, symbol=None, page_index=None, page_size=None):
        """
        参数名称     是否必须  类型   描述
        symbol      false   string "BTC","ETH"...
        page_index  false   int    第几页,不填第一页
        page_size   false   int    不填默认20，不得多于50
        """
        
        params = {}
        if symbol:
            params["symbol"] = symbol
        if page_index:
            params["page_index"] = page_index
        if page_size:
            params["page_size"] = page_size  
    
        request_path = '/api/v1/contract_openorders'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)
    
    
    # 获取合约历史委托
    def get_contract_history_orders(self, symbol, trade_type, type, status, create_date,
                                    page_index=None, page_size=None):
        """
        参数名称     是否必须  类型     描述	    取值范围
        symbol      true	    string  品种代码  "BTC","ETH"...
        trade_type  true	    int     交易类型  0:全部,1:买入开多,2: 卖出开空,3: 买入平空,4: 卖出平多,5: 卖出强平,6: 买入强平,7:交割平多,8: 交割平空
        type        true	    int     类型     1:所有订单、2：结束汏订单
        status      true	    int     订单状态  0:全部,3:未成交, 4: 部分成交,5: 部分成交已撤单,6: 全部成交,7:已撤单
        create_date true	    int     日期     7，90（7天或者90天）
        page_index  false   int     页码，不填默认第1页		
        page_size   false   int     不填默认20，不得多于50
        """
        
        params = {"symbol": symbol,
                  "trade_type": trade_type,
                  "type": type,
                  "status": status,
                  "create_date": create_date}
        if page_index:
            params["page_index"] = page_index
        if page_size:
            params["page_size"] = page_size  
    
        request_path = '/api/v1/contract_hisorders'
        return api_key_post(self.__url, request_path, params, self.__access_key, self.__secret_key)


    def get_open_order(self, account_id, symbol):
        params = {
            "account-id": account_id,
            "symbol": symbol,
            "type": "both",
            "size": 100
        }

        url = self.__url + '/api/v1/order/openOrders'

        return self.http_get_request_with_retry(url, params)


    def give_order_request(self, account_id, amount, price, source, symbol, type_of_trade):
        params = {
            "account-id": account_id,
            "amount": amount,
            "price": price,
            "source": source,
            "symbol": symbol,
            "type": type_of_trade
        }

        url = self.__url + '/api/v1/order/orders/place'

        return self.http_get_request_with_retry(url, params)

    def get_order(self, order_id):
        params = {
            "order-id": order_id
        }

        url = self.__url + '/api/v1/order/openOrders'

        return self.http_get_request_with_retry(url, params)

    # return list {"currency":utsc, "type":"frozen/trade", "amount":""}
    def get_account_balance(self,ACCOUNT_ID):
        return self.http_get_request_with_retry(self._url  + "/v1/account/"+ACCOUNT_ID+"/balance")
