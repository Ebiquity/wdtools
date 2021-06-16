import wd_tools as wdt

test_searches = [
 "wd_search('trump', target_types=['PER'])"
 "wdsearch('letter bomb', category='concept', top=1)"
 "wd_search('tom sawyer', top = 2)"
 "wd_search('tom sawyer', bad_types = ['fictional'], top = 2)"
 "wd_search('tom sawyer', target_types = ['PER'] bad_types = ['fictional'], top = 2)"
 "wd_search('letter bomb', category='concept', top=1)"
 "wd_search('spingfield wisconsin', type = ['LOC'])"
 "wd_search('apple CEO', type = ['PER'], top = 5)"
 "wd_search('apple Cook', type = ['PER'], top = 1)"
 "wd_search('korean war', type=['event'])"
 "wd_search('BMI', category='concept')"
 "wd_search('Trump', target_type=['FAC'])"
 "wd_search('Trump', target_type=['PER'])"
 "wd_search('Trump', target_type=['ORG'])"]

