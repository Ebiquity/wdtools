"""
 add columns with the predictions makde by the linker.
"""

import wd_search as wd
import argparse as ap

def evaluate_column(infile, outfile=None, show_progress=False):
    """ Read in a tab-seperated table of data from a Procure table with annotator data.
        Add columns with links for using context: none, header, and caption.
        Write the results out to a new tsv text file """
    
    def qid(link):  return link['qid'] if link else None
    
    if not outfile:
        outfile = infile + "_linked.txt"

    data_rows = []
    title_row = ['#title', '', '', '', '', '']
    title = ''
    caption_row = ['#caption', '', '', '', '', '']
    caption = ''
    meta_row = ['#meta', 'column', 'annotator', 'no context', 'header', 'caption']
    correct = [0,0,0] # count of correct link for the three cases
    
    # read in the data
    in_rows = [line.strip().split('\t') for line in open(infile)]
    for in_row in in_rows:
        if in_row[0] == '#title':
            title_row = in_row + ['','','']
        elif in_row[0] == '#caption':
            caption_row = in_row + ['','','']
            caption_text = in_row[1]
        elif in_row[0] == '#meta':
            pass
        elif in_row[0] == 'header':
            header_row = in_row 
            header_text = in_row[1]
            header_annotation = in_row[2]
        else:
            data_rows.append(in_row)
    
    # the first three rows remain the same
    out_rows = [title_row, caption_row, meta_row]
    
    # link header
    link1 = qid(wd.link(header_text, context=''))
    link2 = link1
    link3 = qid(wd.link(header_text, context=caption))
    out_row = header_row + [link1, link2, link3]
    if show_progress: print(out_row)
    out_rows.append(out_row)
    
    # link data rows
    for row in data_rows:
        text = row[1]
        annotation = row[2]
        links = [qid(wd.link(text, context='')),
                 qid(wd.link(text, context=header_text)),
                 qid(wd.link(text, context=caption_text))]
        out_row = row + links
        correct = [c+1 if links[n] == annotation else c for n,c in enumerate(correct)]
        if show_progress: print(out_row)
        out_rows.append(out_row)

    # show the accuracy of each of the three linking approaches
    acc_row = ['acc', header_text, '1.0'] + [f"{n/len(data_rows):.2f}" for n in correct]
    if show_progress: print(acc_row)
    out_rows.append(acc_row)
                         
    # write output
    with open(outfile, 'w') as out:
        for row in out_rows:
            print('\t'.join(row), file=out)

    print(f"Wrote output to {outfile}")


if __name__ == '__main__':
    p = ap.ArgumentParser()
    p.add_argument('infile', help='TSV file of one colummn with annotator data')
    p.add_argument('-o', '--outfile', nargs='?', default = None, help='filename for output, a TSV file with link predictions')
    p.add_argument('-s', '--show', nargs='?', default = False, help='show progress as we go')
    args = p.parse_args()
    evaluate_column(args.infile, args.outfile, args.show)
