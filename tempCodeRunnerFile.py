for order_range in order_ranges:
#     for stoploss_val in stoploss_values:
#         stoploss=round(0.01*stoploss_val,2)
#         for day in sorted_dates:
#             SP=None
#             for time in time_values:
#                 if(SP==None):
#                     SP=index_data[index_data['datetime'].apply(lambda x:x.split(' ')[0].strip()==day and x.split(' ')[1]==time)].values[0]
#                     print("Sp: {}".format(SP))