
# PE_order=place_order(tradingSym_PE,"sell",PE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
# CE_order=place_order(tradingSym_CE,"sell",CE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

# CE_price=SP+1500
# PE_price=SP-1500

# tradingSym_PE_1500=symbol+str(PE_price)+"PE"
# tradingSym_CE_1500=symbol+str(CE_price)+"CE"

# if(PE_order): PE_1500=place_order(tradingSym_PE_1500,"buy",PE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
# if(CE_order): CE_1500=place_order(tradingSym_CE_1500,"buy",CE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)

# PE_stoploss_orderid=None
# CE_stoploss_orderid=None
# while True:
#     cur_PE_price=kite.quote(tradingSym_PE)[tradingSym_PE]['last_price']
#     cur_CE_price=kite.quote(tradingSym_CE)[tradingSym_CE]['last_price']
#     if is_current_time_1515():
#         PE_stoploss_orderid=place_order(tradingSym_PE,"buy",cur_PE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
#         CE_stoploss_orderid=place_order(tradingSym_CE,"buy",cur_CE_price,kite.EXCHANGE_NFO,kite.ORDER_TYPE_MARKET,kite.PRODUCT_MIS)
#         break
#     elif ()
