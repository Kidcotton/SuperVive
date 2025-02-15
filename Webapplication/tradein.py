import random


class tradein:
    count_id =0
    def __init__(self,pc_component,types_component,condition,remarks):
        tradein.count_id +=1
        self.__trade_in = tradein.count_id
        self.__pc_component = pc_component
        self.__types_component = types_component
        self.__condition = condition
        self.__remarks = remarks


    def set_remarks(self,remarks):
        self.__remarks = remarks

    def get_remarks(self):
        return self.__remarks

    def set_trade_in(self,trade_in):
        self.__trade_in = trade_in

    def get_trade_in(self):
        return self.__trade_in

    def set_pc_component(self,pc_component):
        self.__pc_component = pc_component

    def set_types_component(self,types_component):
        self.__types_component = types_component

    def set_condition(self,condition):
        self.__condition = condition

    def get_pc_component(self):
        return self.__pc_component

    def get_types_component(self):
        return self.__types_component

    def get_condition(self):
        return self.__condition
