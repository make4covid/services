
import pytest

from .auto_notification import FrontAPIWrapper, OrderProcessedNotification, TrackingInfoNotification
front = FrontAPIWrapper()

import requests

def test_run_order_processed_notification():
    notification = OrderProcessedNotification()
    notification.run()

def test_trackig_info_notification():
    notification = TrackingInfoNotification()
    notification.run()    

def test_list_channels():
    ret = front.channels()
    assert len(ret['_results']) > 3

def test_create_message():
    payload = {
        "sender_name": "Make4Covid",
        "to": ["tom.yeh@colorado.edu"],
        "subject": "test image from pytest",
        "body": "this is a test message"       
    }
    ret = front.create_message('cha_3yb0x', payload)