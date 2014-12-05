# -*- coding: utf-8 -*-

"""Wrap apriori.exe which makes association rule."""

from subprocess import call

# Run Apriori Algorithm
def run_apriori(minsup = 80, 
                minconf = 100, 
                maxrule = 4, 
                input_file = 'apriori_file.txt', 
                output_file_items='apriori_items.txt', 
                output_file_rules='apriori_rules.txt'):
    """Execute association rule mining, using the apriori algorithm.
    
    The output of this function is written in two files, one for 
    frequent itemsets and one file for association rules.
    
    apriori is implemented by Christian Borgelt, 
    (http://www.borgelt.net/apriori.html)
    Keyword arguments:
        minsup = 80, Minimum support of itemsets as a procentage.
        minconf = 100, Minimum confidence of a rule as a procentage.
        maxrule = 4, Maximum number of items per item set/association rule.
        input_file = 'apriori_file.txt' path to file that contains the 
                     transactions to be analysed.
        output_file_items = 'apriori_items.txt' output path for itemsets.
        output_file_rules = 'apriori_rules.txt' output path for assoc. rules.
    """
    status1 = call('apriori.exe -f"," \
                                -s{0} \
                                -v"[Sup. %0S]" {1} {2}'
                                .format(minsup, input_file, output_file_items))
    if status1!=0:
        print('An error occured while calling apriori, \
               a likely cause is that minSup was set to high \
               such that no frequent itemsets were generated or \
               spaces are included in the path to the apriori files.')
        exit()

    print('Mining for associations by the Apriori algorithm')
    status2 = call('apriori.exe -tr \
                                -f"," \
                                -n{0} \
                                -c{1} \
                                -s{2} \
                                -v"[Conf. %0C,Sup. %0S]" {3} {4}'
                                .format(maxrule, minconf, minsup, input_file, output_file_rules))
    if status2!=0:
        print('An error occured while calling apriori')
        exit()
    print('Apriori analysis done')