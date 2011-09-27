import csv

def to_iso(dmy):
    if len(dmy) == 0:
        return dmy
    else:
        return '-'.join([dmy[6:], dmy[3:5], dmy[:2]])

table_ids = {}
for table in ["GSP_Group", "Market_Participant", "Market_Role", "MTC_Meter_Type",
              "MTC_Payment_Type", "Profile_Class", "Standard_Settlement_Configuration",
              "Time_Pattern_Regime"]:
    ids = {}
    table_ids[table] = ids
    with open("original/" + table + ".csv") as fl:
        f = csv.reader(fl)
        with open("converted/" + table + ".csv", "w") as conv:
            converted = csv.writer(conv)
            id = 0
            for line in f:
                if id > 0:
                    ids[line[0]] = id
                    if table == 'MTC_Meter_Type':
                        converted.writerow([id, line[0], line[1], to_iso(line[2]), to_iso(line[3])])
                    elif table == 'MTC_Payment_Type':
                        converted.writerow([id, line[0], line[1], to_iso(line[2]), to_iso(line[3])])
                    elif table == 'Profile_Class':
                        converted.writerow([id] + [line[table_field] for table_field in [0, 2]])
                    elif table == 'Standard_Settlement_Configuration':
                        if line[4] == 'I':
                            is_import = '1'
                        else:
                            is_import = '0'
                        converted.writerow([id, line[0], line[3], is_import, to_iso(line[1]), to_iso(line[2])])
                    elif table == 'Market_Participant':
                        converted.writerow([id] + [line[table_field] for table_field in range(2)])
                    elif table == 'Time_Pattern_Regime':
                        if line[1] == "C":
                            is_teleswitch = '0'
                        else:
                            is_teleswitch = '1'
                        if line[2] == "Y":
                            is_gmt = '1'
                        else:
                            is_gmt = '0'
                        converted.writerow([id, line[0], is_teleswitch, is_gmt])
                    else:
                        converted.writerow([id] + line)
                else:
                    if table == 'Profile_Class':
                        converted.writerow(["Chellow Id"] + [line[table_field] for table_field in [0, 2]])
                    elif table == 'Standard_Settlement_Configuration':
                        converted.writerow(["Chellow Id", line[0], line[3], line[4], line[1], line[2]])
                    elif table == 'Market_Participant':
                        converted.writerow(["Chellow Id"] + [line[table_field] for table_field in range(2)])
                    else:
                        converted.writerow(["Chellow Id"] + line)
                id += 1
            if table == 'Profile_Class':
                converted.writerow([9,"0","Half-hourly"])

with open("original/Clock_Interval.csv") as fl:
    f = csv.reader(fl)
    with open("converted/Clock_Interval.csv", "w") as conv:
        converted = csv.writer(conv)
        id = 0
        for fields in f:
            if id > 0:
                time_fields = []
                for field in fields[-2:]:
                    time_fields += field.split(':')
                converted.writerow([id, table_ids['Time_Pattern_Regime'][fields[0]]] + fields[1:-2] + time_fields)
            else:
                converted.writerow(["Chellow Id","TPR Chellow Id","Day of the Week Id","Start Day","Start Month","End Day","End Month","Start Hour","Start Minute","End Hour","End Minute"])
            id += 1

dno_lookup = {}

with open("original/Market_Participant_Role.csv") as fl:
    f = csv.reader(fl)
    with open("converted/Market_Participant_Role-dno.csv", "w") as fl_dno:
        f_dno = csv.writer(fl_dno)
        with open("converted/Market_Participant_Role-party.csv", "w") as fl_party:
            f_party = csv.writer(fl_party)
            with open("converted/Market_Participant_Role-provider.csv", "w") as fl_provider:
                f_provider = csv.writer(fl_provider)
                id = 0
                for fields in f:
                    if id > 0:
                        dno_code = fields[-1]
                        if len(dno_code) == 0:
                            f_provider.writerow([id])
                        else:
                            f_dno.writerow([id, dno_code])
                            dno_lookup[fields[0]] = id
                        f_party.writerow([id, table_ids['Market_Role'][fields[1]], table_ids['Market_Participant'][fields[0]], fields[4], to_iso(fields[2]), to_iso(fields[3])])
                    else:
                        f_dno.writerow(["Chellow Id","Distributor Short Code"])
                        f_party.writerow(["Chellow Id","Market Participant Role Code Id","Market Participant Chellow Id","Address Line 1","Effective From Date {MPR}","Effective To Date {MPR}"])
                        f_provider.writerow(["Chellow Id"])
                    id += 1
                f_party.writerow([id,22,47,"Dummy 99","1996-04-01",''])
                f_dno.writerow([id, '99'])
                dno_lookup['CUST'] = id

voltage_levels = {
    "LV": "1",
    "HV": "2",
    "EHV": "3"}

with open("original/Line_Loss_Factor_Class.csv") as fl:
    f = csv.reader(fl)
    with open("converted/Line_Loss_Factor_Class.csv", "w") as conv:
        converter = csv.writer(conv)
        id = 0
        for fields in f:
            if id > 0:
                description = fields[5]
                vl_id = voltage_levels["LV"]
                for k, v in voltage_levels.items():
                    if k in description:
                        vl_id = v
                is_substation = '0'
                for pattern in ['_SS', ' SS', ' S/S',  '(S/S)', 'sub', 'Sub']:
                    if pattern in description:
                        is_substation = '1'
                is_import = '1'
                for pattern in ['C', 'D']:
                    if pattern in fields[6]:
                        is_import = '0'
                converter.writerow([id, dno_lookup[fields[0]], fields[3], fields[5], vl_id, is_substation, is_import, to_iso(fields[2]), to_iso(fields[-1])])
            else:
                converter.writerow(["Chellow Id","DNO Chellow Id","Line Loss Factor Class Id","Line Loss Factor Class Description","Voltage Level Id","Is Substation?","Is Import?","Effective From Settlement Date {LLFC}","Effective To Settlement Date {LLFC}"])
            id += 1
        converter.writerow([id, dno_lookup['CUST'],510,"PC 5-8 & HH HV",2,0,1,"1996-04-01",''])
        id += 1
        converter.writerow([id, dno_lookup['CUST'],521,"Export (HV)",2,0,0,"1996-04-01",''])
        id += 1
        converter.writerow([id, dno_lookup['CUST'],570,"PC 5-8 & HH LV",1,0,1,"1996-04-01",''])
        id += 1
        converter.writerow([id, dno_lookup['CUST'],581,"Export (LV)",1,0,0,"1996-04-01",''])
        id += 1
        converter.writerow([id, dno_lookup['CUST'],110,"Profile 3 Unrestricted",1,0,1,"1996-04-01",''])
        id += 1
        converter.writerow([id, dno_lookup['CUST'],210,"Profile 4 Economy 7",1,0,1,"1996-04-01",''])
            
with open("original/Measurement_Requirement.csv") as fl:
    f = csv.reader(fl)
    with open("converted/Measurement_Requirement.csv", "w") as conv:
        converted = csv.writer(conv)
        id = 0
        for fields in f:
            if id > 0:
                converted.writerow([str(id), table_ids['Standard_Settlement_Configuration'][fields[0]], table_ids['Time_Pattern_Regime'][fields[1]]])
            else:
                converted.writerow(["Chellow Id","SSC Chellow Id","TPR Chellow Id"])
            id += 1

with open("converted/Meter_Timeswitch_Class.csv", "w") as conv:
    converted = csv.writer(conv)
    id = 0
    converted.writerow(["Chellow Id","Chellow DNO Id","Meter Timeswitch Class Id","Meter Timeswitch Class Description","Has Related Meter?","Has Comms?","Is HH?","Meter Type Chellow Id","Meter Payment Type Chellow Id","MTC TPR Count","Effective From Settlement Date {MTC}","Effective To Settlement Date {MTC}"])
    with open("original/Meter_Timeswitch_Class.csv") as orig_file:
        f = csv.reader(orig_file)
        for fields in f:
            if id > 0:
                mtc_code = int(fields[0])
                if 499 < mtc_code < 510 or 799 < mtc_code < 1000:
                    if fields[5] == 'T':
                        has_related_meter = '1'
                    else:
                        has_related_meter = '0'
                    if fields[8] == 'Y':
                        has_comms = '1'
                    else:
                        has_comms = '0'
                    if fields[9] == 'H':
                        is_hh = '1'
                    else:
                        is_hh = '0'
                    meter_type_id = table_ids['MTC_Meter_Type'][fields[6]]
                    payment_type_id = table_ids['MTC_Payment_Type'][fields[7]]
                    converted.writerow([id, "", fields[0], fields[3], has_related_meter, has_comms, is_hh, meter_type_id, payment_type_id, fields[10], to_iso(fields[1]), to_iso(fields[2])])
            id += 1

    with open("original/MTC_in_PES_Area.csv") as orig_file:
        f = csv.reader(orig_file)
        is_first = True
        for fields in f:
            if is_first:
                is_first = False
            else:
                mtc_code = int(fields[0])
                if not (499 < mtc_code < 510 or 799 < mtc_code < 1000):
                    if mtc_code > 500:
                        has_related_meter = '1'
                    else:
                        has_related_meter = '0'
                    if fields[8] == 'Y':
                        has_comms = '1'
                    else:
                        has_comms = '0'
                    if fields[9] == 'H':
                        is_hh = '1'
                    else:
                        is_hh = '0'
                    dno_id = dno_lookup[fields[2]]
                    meter_type_id = table_ids['MTC_Meter_Type'][fields[6]]
                    payment_type_id = table_ids['MTC_Payment_Type'][fields[7]]
                    converted.writerow([id, dno_id, fields[0], fields[5], has_related_meter, has_comms, is_hh, meter_type_id, payment_type_id, fields[10], to_iso(fields[1]), to_iso(fields[4])])
            id += 1