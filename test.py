import dateparser

date_string = "aujourd'hui"
parsed_date = dateparser.parse(date_string, languages=['fr'])
print(parsed_date)
