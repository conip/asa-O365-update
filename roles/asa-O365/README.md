asa-O365
=========

Role allows to update standard ACL or object-group type network based on published by Microsoft list of IPv4 (only).
example of such update: 
https://endpoints.office.com/endpoints/Worldwide?clientRequestID=e8df34c7-cacb-43c6-be5a-7e6b11f23a5b

information about version check is stored in temporary file 
i.e.
/tmp/endpoints_clientid_latestversion.txt
"050f86bf-2a6b-4d8e-af2a-58d4576ea473
2020090100"

If version is up to date (published vs latest check stored on localhost) file containing "./update_files/o365_version_xxxxxxxxxx.txt" will not be created or replaced if already exisitng.  
"endpoints_clientid_latestversion.txt" needs to be deleted to enforce such action. 

IMPORTANT
------------
- code when doing object update (regardless the type) deletes it and adds again. Whatever is listed in the object not in regards to Microsoft's IP list will be lost. 

Requirements
------------
- server requires Internet access to "https://endpoints.office.com" 


Role Variables
--------------
```
var_object_type: "standard-acl" | "object-group"
var_object_name: "name of object to be udpated"
var_allow_LAN: true
```
If standard ACL is used for SPLIT ACL for VPN purpose we can allow local access i.e. printing. var_allow_LAN: TRUE adds host 0.0.0.0 entry to ACL or OBJECT-GROUP 



Dependencies
------------

Dependent on module: "check_O365_updates.py"
Module located in the role's /library/ folder.
Can be executed on a seperate play if more ASAs are in inventory or directly from the role.
To invoke directly from the role the following block of the code needs to be uncommented (roles/asa-O365/main.yml)
```
# - name: CHECKING FOR THE NEWEST VERSION AND IF NEW AVAILABLE - SAVING TO FILE "./update_files/o365_version_xxxxxxxxxx.txt"
#  local_action:
#    module: check_O365_updates
#  register: version_result

# - set_fact:
#    var_version: "{{ version_result['meta'] }}"
```

Example Playbook
----------------

Example 1:
```
- name: UPDATING ASA
  hosts: asa
  connection: network_cli
  gather_facts: false
  become_method: enable
  roles:
    - role: asa-O365
      var_object_type: "standard-acl"
      var_object_name: "Ensono-O365-Split"
      var_version: "{{ hostvars['localhost']['version_result']['meta'] }}"
```
Example 2:
```
- name: CHECKING FOR THE NEWEST VERSION AND IF NEW AVAILABLE - SAVING TO FILE
  hosts: localhost
  tasks:
  - name: EXECUTING MODULE "check_O365_updates"
    check_O365_updates:
    register: version_result
  - debug: var=version_result

- name: CHECKING VARIABLES
  hosts: asa
  gather_facts: false
  tasks:
    - set_fact:
        var_object_type: "{{ hostvars[inventory_hostname].var_object_type }}"
        var_object_name: "{{ hostvars[inventory_hostname].var_object_name }}"
        var_allow_LAN: "{{ hostvars[inventory_hostname].var_allow_LAN }}"

- name: UPDATING ASA
  hosts: asa
  connection: network_cli
  gather_facts: false
  become_method: enable
  roles:
    - role: asa-O365
      var_version: "{{ hostvars['localhost']['version_result']['meta'] }}"
```
License
-------

BSD

Author Information
------------------

Przemyslaw Konitz (pkonitz@gmail.com)
