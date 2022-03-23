#!/bin/bash

(crontab -l 2>/dev/null; echo "0 */2 * * * main.py --create") | crontab -
(crontab -l 2>/dev/null; echo "0 0 * * 0 main.py --scrape") | crontab -
