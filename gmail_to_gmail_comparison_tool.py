#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Gmail to Gmail Comparison & Audit Tool (Robust)
================================================================================
Author:       Tino Höhne
Repository:   Agent47-Scripts/gmail-to-gmail-comparison-tool
Version:      1.0.1
License:      MIT License

Description:
Production-grade IMAP comparison and audit utility featuring auto-reconnect logic,
socket-error recovery (EOF handling), and mUTF-7 folder decoding for accurate 
side-by-side message count verification between Gmail / Google Workspace accounts.
================================================================================
"""

__version__ = "1.0.1"

import os
import sys
import ssl
import imaplib
import time
import socket
import base64

# ==============================================================================
# 1. ENVIRONMENT CONFIGURATION & CREDENTIAL RETRIEVAL
# ==============================================================================
# Retrieve and validate IMAP connection parameters securely from environment variables.
SRC_HOST = os.getenv("SRC_HOST", "imap.gmail.com")
SRC_USER = os.getenv("SRC_USER")
SRC_PASS = os.getenv("SRC_PASS")

TGT_HOST = os.getenv("TGT_HOST", "imap.gmail.com")
TGT_USER = os.getenv("TGT_USER")
TGT_PASS = os.getenv("TGT_PASS")


# ==============================================================================
# 2. CORE PROTOCOL & CONNECTION FUNCTIONS
# ==============================================================================

def connect_imap(host, user, password):
    """
    Establishes a secure SSL/TLS IMAP connection wrapped in an infinite retry loop 
    to handle transient network drops, high latency, or server-side timeouts.
    """
    print(f"[*] Connecting to server {host} with user {user}...")
    while True:
        try:
            context = ssl.create_default_context()
            conn = imaplib.IMAP4_SSL(host, port=993, ssl_context=context)
            conn.login(user, password)
            return conn
        except Exception as e:
            print(f"  [!] Connection failed to {host} ({e}). Retrying in 5 seconds...")
            time.sleep(5)


def decode_mutf7(folder_bytes):
    """
    Safely decodes mUTF-7 encoded IMAP folder names containing non-ASCII characters 
    (e.g., German umlauts) into clean, standard Unicode strings.
    """
    if isinstance(folder_bytes, bytes):
        folder_bytes = folder_bytes.decode('latin1', errors='ignore')
    
    res = []
    i = 0
    n = len(folder_bytes)
    while i < n:
        if folder_bytes[i] == '&':
            j = folder_bytes.find('-', i)
            if j == -1:
                res.append(folder_bytes[i:])
                break
            if j == i + 1:
                res.append('&')
            else:
                b64_part = folder_bytes[i+1:j].replace(',', '/')
                pad = (-len(b64_part)) % 4
                b64_part += '=' * pad
                try:
                    decoded = base64.b64decode(b64_part.encode('ascii')).decode('utf-16be')
                    res.append(decoded)
                except Exception:
                    res.append(folder_bytes[i:j+1])
            i = j + 1
        else:
            res.append(str(folder_bytes[i]))
            i += 1
    return "".join(res)


def clean_folder_name(folder_str):
    """
    Extracts and decodes clean folder paths from IMAP list responses.
    """
    if isinstance(folder_str, bytes):
        folder_str = folder_str.decode('utf-8', errors='ignore')
    parts = folder_str.split('"')
    if len(parts) >= 3:
        return decode_mutf7(parts[-2])
    return decode_mutf7(folder_str.strip())


def get_folder_counts(host, user, password, label):
    """
    Retrieves all folders and message counts with bulletproof reconnect and EOF recovery logic.
    """
    # Initialize robust SSL connection
    conn = connect_imap(host, user, password)
    print(f"[*] Fetching and analyzing folder message counts from {label} account...")
    
    # Retrieve folder list with retry safety against socket/EOF drops
    status = None
    data = None
    for attempt in range(3):
        try:
            status, data = conn.list()
            if status == 'OK':
                break
        except (socket.error, ssl.SSLEOFError, imaplib.IMAP4.abort, EOFError) as e:
            print(f"  [!] Connection dropped during LIST (Attempt {attempt+1}/3: {e}). Reconnecting...")
            try:
                conn.logout()
            except:
                pass
            time.sleep(2)
            conn = connect_imap(host, user, password)
            
    if status != 'OK' or not data:
        print("[!] Error listing folders after multiple attempts.")
        try:
            conn.logout()
        except:
            pass
        return {}

    folder_counts = {}
    
    # Iterate through discovered mailboxes and count messages per folder
    for response in data:
        if not response:
            continue
        raw_name = clean_folder_name(response)
        
        # Filter out standard system trash and spam directories
        normalized_folder_name = raw_name.lower()
        if any(sys_keyword in normalized_folder_name for sys_keyword in ['trash', 'deleted', 'junk', 'spam']):
            continue

        # Fetch message count per folder with robust retry handling
        msg_count = 0
        for attempt in range(3):
            try:
                status, _ = conn.select(f'"{raw_name}"', readonly=True)
                if status == 'OK':
                    status, search_data = conn.search(None, 'ALL')
                    if status == 'OK' and search_data and search_data[0]:
                        msg_count = len(search_data[0].split())
                break
            except (socket.error, ssl.SSLEOFError, imaplib.IMAP4.abort, EOFError) as e:
                print(f"  [!] Socket drop on folder {raw_name} (Attempt {attempt+1}/3). Reconnecting...")
                try:
                    conn.logout()
                except:
                    pass
                time.sleep(2)
                conn = connect_imap(host, user, password)
            except Exception:
                break
                
        folder_counts[raw_name] = msg_count

    # Gracefully logout after gathering metrics
    try:
        conn.logout()
    except:
        pass
        
    return folder_counts


# ==============================================================================
# 3. MAIN EXECUTION & REPORTING PIPELINE
# ==============================================================================

def main():
    """
    Main orchestration function validating credentials, executing side-by-side 
    folder metrics gathering, and printing the formatted comparison report.
    """
    if not all([SRC_USER, SRC_PASS, TGT_USER, TGT_PASS]):
        print("[-] Error: Missing required environment variables for source or target accounts.")
        sys.exit(1)

    # Fetch mailbox metrics from both accounts independently
    source_counts = get_folder_counts(SRC_HOST, SRC_USER, SRC_PASS, "Source")
    target_counts = get_folder_counts(TGT_HOST, TGT_USER, TGT_PASS, "Target")

    # Combine unique folders for comprehensive comparison mapping
    all_discovered_folders = sorted(list(set(source_counts.keys()).union(set(target_counts.keys()))))

    # Print formatted output table header
    print("\n" + "=" * 65)
    print(f"{'Folder Name':<35} | {'Source':<8} | {'Target':<8} | {'Status'}")
    print("=" * 65)

    discrepancy_detected = False
    
    # Evaluate and print comparison results row by row
    for current_folder in all_discovered_folders:
        source_count = source_counts.get(current_folder, 0)
        target_count = target_counts.get(current_folder, 0)
        
        if source_count == target_count:
            audit_status = "MATCH OK"
        else:
            audit_status = "MISMATCH!"
            discrepancy_detected = True

        print(f"{current_folder[:35]:<35} | {source_count:<8} | {target_count:<8} | {audit_status}")

    # Output final audit status summary
    print("=" * 65)
    if discrepancy_detected:
        print("[!] Audit Warning: Discrepancies detected between source and target mailboxes.")
    else:
        print("[+] Audit Success: All folder counts and message totals match perfectly!")


if __name__ == "__main__":
    main()
