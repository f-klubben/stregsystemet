from datetime import datetime

def start_of(date):
    return datetime(date.year, date.month, date.day)

def end_of(date):
    return datetime(date.year, date.month, date.day, 23, 59)
