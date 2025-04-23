#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易信号机器人主程序入口

此文件仅包含程序的入口点，所有初始化逻辑已移至core模块
"""

from core import initialize_bot

if __name__ == "__main__":
    initialize_bot() 