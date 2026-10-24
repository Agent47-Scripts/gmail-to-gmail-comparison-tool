#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
IMAP Migration Verification and Audit Tool
================================================================================
Author:       Tino Höhne
Repository:   Agent47-Scripts/gmail-to-gmail-comparison-tool
Version:      1.0.0
License:      MIT License

Description:
This script connects securely to a source and a target IMAP server (such as
iCloud to Gmail or Gmail to Gmail environments). It queries mailbox structures
and retrieves message counts side-by-side to audit and verify that no data loss
has occurred during email migration or backup procedures.
================================================================================
"""

__version__ = "1.0.0"

import os
import sys
import imaplib
import ssl

# ==============================================================================
# 1. ENVIRONMENT CONFIGURATION & CREDENTIAL RETRIEVAL
# ==============================================================================
# Retrieve source and target connection parameters from environment variables.
# Default values are configured for iCloud source and Gmail target endpoints.
SRC_HOST = os.getenv("SRC_HOST", "imap.mail.me.com")
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
    Establishes a secure SSL/TLS encrypted connection to the specified IMAP host
    and authenticates using the provided user credentials.
    
    Parameters:
        host (str): The IMAP server hostname.
        user (str): The account username or email address.
        password (str): The account password or application-specific password.
        
    Returns:
        imaplib.IMAP4_SSL: An authenticated IMAP connection object.
    """
    print(f"[*] Connecting to server {host} with user {user}...")
    
    # Initialize a secure default SSL context for encrypted communication
    ssl_context = ssl.create_default_context()
    
    try:
        # Open secure IMAP socket connection
        mail_connection = imaplib.IMAP4_SSL(host, ssl_context=ssl_context)
        
        # Authenticate against the IMAP server
        mail_connection.login(user, password)
        return mail_connection
        
    except Exception as connection_error:
        print(f"[-] Critical connection or authentication failure to {host}: {connection_error}")
        sys.exit(1)


def get_folder_counts(mail_conn):
    """
    Retrieves all available mailboxes and folders from an IMAP server and counts
    the total number of messages contained within each folder.
    
    Parameters:
        mail_conn (imaplib.IMAP4_SSL): An active and authenticated IMAP connection.
        
    Returns:
        dict: A dictionary mapping folder names to their corresponding message counts.
    """
    folder_message_counts = {}
    
    try:
        # Request the full list of mailboxes from the server
        status_response, folder_list = mail_conn.list()
        
        if status_response != 'OK':
            print("[-] Failed to retrieve mailbox folder list from server.")
            return folder_message_counts

        # Iterate through each raw folder entry returned by the IMAP server
        for folder_entry in folder_list:
            
            # Decode the raw byte string safely into a standard unicode string
            decoded_entry = folder_entry.decode('utf-8', errors='ignore')
            
            # Parse folder name utilizing standard IMAP LIST response delimiters
            path_parts = decoded_entry.split(' "/" ')
            if len(path_parts) < 2:
                # Fallback delimiter check for alternative server configurations
                path_parts = decoded_entry.split(' "." ')
            
            if len(path_parts) >= 2:
                folder_name = path_parts[1].strip('"')
            else:
                folder_name = decoded_entry.split()[-1].strip('"')

            # Filter out standard system trash and spam directories to keep audit clean
            normalized_folder_name = folder_name.lower()
            if any(sys_keyword in normalized_folder_name for sys_keyword in ['trash', 'deleted', 'junk', 'spam']):
                continue

            # Attempt to fetch message counts using the fast IMAP STATUS command
            try:
                status_res, status_data = mail_conn.status(f'"{folder_name}"', "(MESSAGES)")
                
                if status_res == 'OK' and status_data:
                    count_string = status_data[0].decode('utf-8')
                    
                    if "MESSAGES" in count_string:
                        # Extract integer message count from server status response
                        message_count_value = int(count_string.split("MESSAGES")[1].strip(" ()"))
                        folder_message_counts[folder_name] = message_count_value
                        
            except Exception:
                # Fallback mechanism: Use SELECT and SEARCH commands if STATUS fails
                try:
                    select_res, _ = mail_conn.select(f'"{folder_name}"', readonly=True)
                    
                    if select_res == 'OK':
                        search_res, search_data = mail_conn.search(None, 'ALL')
                        
                        if search_res == 'OK' and search_data and search_data[0]:
                            message_ids = search_data[0].split()
                            folder_message_counts[folder_name] = len(message_ids)
                        else:
                            folder_message_counts[folder_name] = 0
                            
                except Exception as inner_error:
                    print(f"[-] Warning: Unable to inspect folder '{folder_name}': {inner_error}")

    except Exception as outer_error:
        print(f"[-] Error encountered while processing folder counts: {outer_error}")
    
    return folder_message_counts


# ==============================================================================
# 3. MAIN EXECUTION & REPORTING PIPELINE
# ==============================================================================

def main():
    """
    Main orchestration function that validates environment variables, initiates
    connections to both source and target accounts, gathers mailbox statistics,
    and prints a comprehensive comparison audit table.
    """
    # Verify that all required authentication credentials are provided in the environment
    if not all([SRC_USER, SRC_PASS, TGT_USER, TGT_PASS]):
        print("[-] Error: Missing required environment variables for source or target accounts.")
        print("    Please set credentials using the following pattern:")
        print("    export SRC_USER='...' && export SRC_PASS='...'")
        print("    export TGT_USER='...' && export TGT_PASS='...'")
        sys.exit(1)

    # Establish secure connections to both source and target mail servers
    source_connection = connect_imap(SRC_HOST, SRC_USER, SRC_PASS)
    target_connection = connect_imap(TGT_HOST, TGT_USER, TGT_PASS)

    print("\n[*] Fetching and analyzing folder message counts from Source account...")
    source_counts = get_folder_counts(source_connection)

    print("\n[*] Fetching and analyzing folder message counts from Target account...")
    target_counts = get_folder_counts(target_connection)

    # Safely close IMAP sessions
    try:
        source_connection.logout()
    except Exception:
        pass
        
    try:
        target_connection.logout()
    except Exception:
        pass

    # Print formatted header for side-by-side ASCII comparison report
    print("\n" + "=" * 65)
    print(f"{'Folder Name':<35} | {'Source':<8} | {'Target':<8} | {'Status'}")
    print("=" * 65)

    # Combine and sort all unique folder names discovered across both accounts
    all_discovered_folders = sorted(list(set(source_counts.keys()).union(set(target_counts.keys()))))
    
    discrepancy_detected = False
    
    # Evaluate counts folder by folder
    for current_folder in all_discovered_folders:
        source_count = source_counts.get(current_folder, 0)
        target_count = target_counts.get(current_folder, 0)
        
        # Check if message quantities match perfectly
        if source_count == target_count:
            audit_status = "MATCH OK"
        else:
            audit_status = "MISMATCH!"
            discrepancy_detected = True

        # Print row entry with strict string truncation to maintain layout alignment
        print(f"{current_folder[:35]:<35} | {source_count:<8} | {target_count:<8} | {audit_status}")

    print("=" * 65)
    
    # Final audit verdict output
    if discrepancy_detected:
        print("[!] Audit Warning: Discrepancies detected between source and target mailboxes.")
    else:
        print("[+] Audit Success: All folder counts and message totals match perfectly!")


if __name__ == "__main__":
    main()