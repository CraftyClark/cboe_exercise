import configparser
import logging

"""
CBOE BATCH TEAM - Python Coding Sample

Please write a program using only the standard Python library which reads PITCH data from standard input, 
and at the end of the input, shows a table of the top ten symbols by shares traded volume.
In short, you'll need to read Add Order messages and remember what orders are open 
so you can apply Order Cancel and Order Executed messages. Trade Messages are sent 
for orders which were hidden. You'll need to use both Order Executed and Trade Messages 
to compute total volume. For simplicity, ignore any Trade Break and long messages ('B', 'r', 'd').

Andrew Clark
"""

class PitchData:
    def __init__(self) -> None:
        """
        .self.existing_orders <dict> = {order_id: {stock_symbol: shares}, order_id: {stock_symbol: shares},...} 
        .self.executed_orders <dict> = {stock_symbol: shares, stock_symbol: shares,...}"""
        self.existing_orders = {}
        self.executed_orders = {}

        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger(__name__)

        config = configparser.RawConfigParser()
        config.read('config.cfg')
        self.data_file = config.get('Data','ImportDataFile')
        self.message_type_index = int(config.get('Pitch Specification', 'MessageTypeIndex'))

        self.addorder_orderid_offset = int(config.get('Pitch Specification','AddOrder_OrderID_Offset'))
        self.addorder_orderid_lastindex = self.addorder_orderid_offset + int(config.get('Pitch Specification','AddOrder_OrderID_Length'))
        self.addorder_shares_offset = int(config.get('Pitch Specification','AddOrder_Shares_Offset'))
        self.addorder_shares_lastindex = self.addorder_shares_offset + int(config.get('Pitch Specification','AddOrder_Shares_Length'))
        self.addorder_stocksymbol_offset = int(config.get('Pitch Specification','AddOrder_StockSymbol_Offset'))
        self.addorder_stocksymbol_lastindex = self.addorder_stocksymbol_offset + int(config.get('Pitch Specification','AddOrder_StockSymbol_Length'))

        self.cancelorder_orderid_offset = int(config.get('Pitch Specification','CancelOrder_OrderID_Offset'))
        self.cancelorder_orderid_lastindex = self.cancelorder_orderid_offset + int(config.get('Pitch Specification','CancelOrder_OrderID_Length'))
        self.cancelorder_cancelshares_offset = int(config.get('Pitch Specification','CancelOrder_CanceledShares_Offset'))
        self.cancelorder_cancelshares_lastindex = self.cancelorder_cancelshares_offset + int(config.get('Pitch Specification','CancelOrder_CanceledShares_Length'))

        self.executeorder_orderid_offset = int(config.get('Pitch Specification','ExecuteOrder_OrderID_Offset'))
        self.executeorder_orderid_lastindex = self.executeorder_orderid_offset + int(config.get('Pitch Specification','ExecuteOrder_OrderID_Length'))
        self.executeorder_executedshares_offset = int(config.get('Pitch Specification','ExecuteOrder_ExecutedShares_Offset'))
        self.executeorder_executedshares_lastindex = self.executeorder_executedshares_offset + int(config.get('Pitch Specification','ExecuteOrder_ExecutedShares_Length'))

        self.tradeorder_shares_offset = int(config.get('Pitch Specification','TradeOrder_Shares_Offset'))
        self.tradeorder_shares_lastindex = self.tradeorder_shares_offset + int(config.get('Pitch Specification','TradeOrder_Shares_Length'))
        self.tradeorder_stocksymbol_offset = int(config.get('Pitch Specification','TradeOrder_StockSymbol_Offset'))
        self.tradeorder_stocksymbol_lastindex = self.tradeorder_stocksymbol_offset + int(config.get('Pitch Specification','TradeOrder_StockSymbol_Length'))


    def update_executed_orders(self, stock_symbol, shares):
        """Update Executed Orders dictionary 
        .stock_symbol <string> = stock ticker
        .shares <int> = number of shares
        """
        # if stock symbol exist in executed orders, add to previous balance
        if stock_symbol in self.executed_orders:
            self.executed_orders[stock_symbol] += shares
        # if stock symbol does not exist, create new entry
        else:
            self.executed_orders[stock_symbol] = shares

        self.logger.info(f'Update Executed Orders Dict Success -> shares_added: {shares}, stock_symbol: {stock_symbol}')


    def add_order(self, message):
        """Add Order to Existing Orders dictionary using the stock_symbol and shares values
        .message <string> = line data from the import data file, of message type Add Order
        """
        order_id = message[self.addorder_orderid_offset:self.addorder_orderid_lastindex]
        shares = int(message[self.addorder_shares_offset:self.addorder_shares_lastindex])
        stock_symbol = message[self.addorder_stocksymbol_offset:self.addorder_stocksymbol_lastindex].strip()

        self.existing_orders[order_id] = {'stock_symbol': stock_symbol, 'shares': shares}

        self.logger.info(f'Add Order Success -> shares_added: {shares}, stock_symbol: {stock_symbol}')


    # Order Cancel messages are sent when a visible order on the Cboe book is canceled in whole or in part.
    def cancel_order(self, message):
        """
        Reduces shares or removes Existing Orders while handling a Cancel Order with the same Order_id.
        .message <string> = line data from the import data file, of message type Cancel Order"""
        order_id = message[self.cancelorder_orderid_offset:self.cancelorder_orderid_lastindex]
        canceled_shares = int(message[self.cancelorder_cancelshares_offset:self.cancelorder_cancelshares_lastindex])

        # If order exist, cancel shares
        if order_id in self.existing_orders:
            previous_shares_count = int(self.existing_orders[order_id]['shares'])
            stock_symbol = self.existing_orders[order_id]['stock_symbol']
            share_count_difference = previous_shares_count - canceled_shares
            # if all shares have been canceled, removed order
            if share_count_difference == 0:
                del self.existing_orders[order_id]
                self.logger.info(f'Cancel Order Success -> canceled_shares: {canceled_shares}, stock_symbol: {stock_symbol}')
            elif share_count_difference < 0:
                # Attempting to cancel more shares than which are available
                self.logger.warning(f'Order_id: {order_id}, Attempted to Cancel {canceled_shares} shares from a Balance of {previous_shares_count} available')
            else:
                # Order will not be removed. Adjust remaining shares on order to correct value
                self.existing_orders[order_id].update({'shares': share_count_difference})
                self.logger.info(f'Partial Cancel Order Success -> canceled_shares: {canceled_shares}, remaining_shares: {share_count_difference}, stock_symbol: {stock_symbol}')

        else:
            self.logger.warning(f'Could not cancel {canceled_shares} for order id {order_id}. Order id did not exist.')


    def execute_order(self, message):
        """Reduces shares or removes Existing Orders while handling an Execute Order with the same Order_id.
        Update Executed Dictionary with the new trade order data.
        .message <string> = line data from the import data file, of message type Execute Order"""
        order_id = message[self.executeorder_orderid_offset:self.executeorder_orderid_lastindex]
        executable_shares = int(message[self.executeorder_executedshares_offset:self.executeorder_executedshares_lastindex])

        # If order exist, execute shares
        if order_id in self.existing_orders:
            previous_shares_count = int(self.existing_orders[order_id]['shares'])
            stock_symbol = self.existing_orders[order_id]['stock_symbol']
            share_count_difference = previous_shares_count - executable_shares
            # if all shares have been executed, add to execution orders and remove order
            if share_count_difference == 0:
                self.update_executed_orders(stock_symbol, executable_shares)
                del self.existing_orders[order_id]
                self.logger.info(f'Execute Order Success & Order {order_id} Removed -> executed_shares: {executable_shares}, stock_symbol: {stock_symbol}')

            elif share_count_difference < 0:
                # Attempting to cancel more shares than which are available
                self.logger.warning(f'Order_id: {order_id}, Attempted to Execute {executable_shares} shares from a Balance of {previous_shares_count} available')

            else:
                self.update_executed_orders(stock_symbol, executable_shares)

                # Order will not be removed. Adjust remaining shares on order to correct value
                self.existing_orders[order_id].update({'shares': share_count_difference})
            
                self.logger.info(f'Execute Order Success -> executed_shares: {executable_shares}, remaining_shares: {share_count_difference}, stock_symbol: {stock_symbol}')

        else:
            self.logger.warning(f'Could not execute {executable_shares} for order id {order_id}. Order id did not exist.')


    def trade_order(self, message):
        """Adds current trade order to the existing Executed Orders Dictionary
        .message <string> = line data from the import data file, of message type Trade Order"""
        shares = int(message[self.tradeorder_shares_offset:self.tradeorder_shares_lastindex])
        stock_symbol = message[self.tradeorder_stocksymbol_offset:self.tradeorder_stocksymbol_lastindex].strip()
        self.update_executed_orders(stock_symbol, shares)

        self.logger.info(f'Trade Order Success -> shares: {shares}, stock_symbol: {stock_symbol}')


    def main(self, datafile):
        """Import Data File and execute appropriate method for each line of data
        based on the message type.
        """
        message_type_dict = {
            'A': self.add_order,
            'E': self.execute_order,
            'X': self.cancel_order,
            'P': self.trade_order
        }

        with open(datafile) as file:
            self.logger.info(f'---Started reading datafile "{datafile}"---')

            for line_data in file:
                # Note that each line in the sample file begins with an extra character, 
                # 'S', not mentioned in the specification. That can be ignored.
                if line_data[0] == 'S':
                    line_data = line_data[1:]

                # message type
                message_type = line_data[self.message_type_index]

                # Determine which method to execute based on message type
                method_selection = message_type_dict.get(message_type)
                method_selection(line_data)

            self.logger.info(f'---Finished reading datafile "{datafile}"---')

        # convert dictionary to list and then sort by shares
        total_traded_volume_list = list(c.executed_orders.items())
        total_traded_volume_list.sort(key=lambda x:x[1], reverse=True)
        
        # print top 10 traded symbols
        template = "{0:6}   {1:20}"
        for i in range(0,10):
            print(template.format(*total_traded_volume_list[i]))


if __name__ == '__main__':
    c = PitchData()
    c.main(c.data_file)
