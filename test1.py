#!/usr/bin/env python
# -*- coding: utf-8 -*-

class People:
    def __init__(self, _Height, __Weight, _Age):
        self.Height = _Height
        self.Weight = _Height
        self.Age = _Age
        self.heheda=_Age

    def _ceshi(self):
        return self.Height,self.Height,self.Age

a = People(173, 80, 35)
result = a._ceshi()
print(result)