import sys
import os
import json
import spacy
import random
from collections import defaultdict

random.seed(2020)

dm_single_close_quote = u'\u2019' # unicode
dm_double_close_quote = u'\u201d'
END_TOKENS = ['.', '!', '?', '...', "'", "`", '"', dm_single_close_quote, dm_double_close_quote, ")"] # acceptable ways to end a sentence

# We use these to separate the summary sentences in the .bin datafiles
# SENTENCE_START = '<s>'
# SENTENCE_END = '</s>'

bbc_tokenized_stories_dir = "/disk/ocean/public/corpora/XSum/bbc-tokenized-segmented-final/"

finished_files_dir = "../data-convs2s"

# Load JSON File : training, dev and test splits.
with open("../XSum-Dataset/XSum-TRAINING-DEV-TEST-SPLIT-90-5-5.json") as json_data:
  train_dev_test_dict = json.load(json_data)

def read_text_file(text_file):
  lines = []
  with open(text_file, "r") as f:
    for line in f:
      lines.append(line.strip())
  return lines

def fix_missing_period(line):
  """Adds a period to a line that is missing a period"""
  if "@highlight" in line: return line
  if line=="": return line
  if line[-1] in END_TOKENS: return line
  # print line[-1]
  return line + " ."

def get_data_from_file(story_file):
  lines = read_text_file(story_file)

  # Lowercase everything
  lines = [line.lower() for line in lines]

  # Put periods on the ends of lines that are missing them (this is a problem in the dataset because many image captions don't end in periods; consequently they end up in the body of the article as run-on sentences)
  lines = [fix_missing_period(line) for line in lines]

  # Make article into a single string
  article = ' '.join(lines)

  return article

def get_article_summary_from_file_and_anonymize(articlefile, summaryfile):
    entityDict = {} # {'@entity1':'Apple'}
    entityDict_rev = {} # {'Apple':'@entity1'}
    entitySet = set()
    entityIdx_article = [] # [('Apple',0,5)]
    entityIdx_summary = []
    article_lines = read_text_file(articlefile)
    summary_lines = read_text_file(summaryfile)
    article_lines = [fix_missing_period(line) for line in article_lines]
    summary_lines = [fix_missing_period(line) for line in summary_lines]
    article = ' '.join(article_lines)
    summary = ' '.join(summary_lines)
    # obtain the ent text using spaCy model
    doc = nlp(article)
    for ent in doc.ents:
        entitySet.add(ent.text)
        entityIdx_article.append((ent.text, ent.start_char, ent.end_char))
    # do the same for summary
    doc = nlp(summary)
    for ent in doc.ents:
        entitySet.add(ent.text)
        entityIdx_summary.append((ent.text, ent.start_char, ent.end_char))
    entityId = [i for i in range(len(entitySet))]
    random.shuffle(entityId)
    idx_offset_article = 0  # need this because after 1st iter idx will be changed
    idx_offset_summary = 0
    for i, entity in enumerate(entitySet):
        entitytag = '@entity'+str(entityId[i])
        entityDict[entitytag] = entity
        entityDict_rev[entity] = entitytag
    # replace this entity in article/summary with entity tag
    for entity, start_idx, end_idx in entityIdx_article:
        start_idx += idx_offset_article
        end_idx += idx_offset_article
        article = article[:start_idx] + entityDict_rev[entity] + article[end_idx:]
        idx_offset_article += len(entityDict_rev[entity]) - len(entity)
    for entity, start_idx, end_idx in entityIdx_summary:
        start_idx += idx_offset_summary
        end_idx += idx_offset_summary
        summary = summary[:start_idx] + entityDict_rev[entity] + summary[end_idx:]
        idx_offset_summary += len(entityDict_rev[entity]) - len(entity)

    return article.lower(), summary.lower(), entityDict

def write_to_bin(data_type, out_file_rb, out_file_fs):
  
  """Reads all the bbids and write them to out file."""
  print("Making text file for bibids listed as %s..." % data_type)
  
  bbcids = train_dev_test_dict[data_type]
  num_stories = len(bbcids)

  rb_foutput = open(out_file_rb, "w")
  fs_foutput = open(out_file_fs, "w")
      
  for idx,s in enumerate(bbcids):
    
    if idx % 1000 == 0:
      print("Writing story %i of %i; %.2f percent done" % (idx, num_stories, float(idx)*100.0/float(num_stories)))

    # Files
    restbodyfile = bbc_tokenized_stories_dir + "/restbody/" + s + ".restbody"
    firstsentencefile = bbc_tokenized_stories_dir + "/firstsentence/" + s + ".fs"
    
            
    # Get the strings to write to .bin file
    abstract = get_data_from_file(firstsentencefile)
    article = get_data_from_file(restbodyfile)
    article = " ".join(article.strip().split()[:400])

    rb_foutput.write(article+"\n")
    fs_foutput.write(abstract+"\n")
    
  rb_foutput.close()
  fs_foutput.close()
    
  print("Finished writing file %s, %s\n" %(out_file_rb, out_file_fs))

def write_to_bin_anonymized(data_type, out_file_rb, out_file_fs):
  """Reads all the bbids and write them to out file."""
  print("Making text file for bibids listed as %s..." % data_type)

  bbcids = train_dev_test_dict[data_type]
  num_stories = len(bbcids)

  rb_foutput = open(out_file_rb, "w")
  fs_foutput = open(out_file_fs, "w")

  for idx, s in enumerate(bbcids):

    if idx % 1000 == 0:
      print("Writing story %i of %i; %.2f percent done" % (idx, num_stories, float(idx) * 100.0 / float(num_stories)))

    # Files
    restbodyfile = bbc_tokenized_stories_dir + "/restbody/" + s + ".restbody"
    firstsentencefile = bbc_tokenized_stories_dir + "/firstsentence/" + s + ".fs"
    entityfile = finished_files_dir + "/entitymapping/" + s + ".ent"

    # Get the strings to write to .bin file
    # abstract = get_data_from_file(firstsentencefile)
    # article = get_data_from_file(restbodyfile)
    # article = " ".join(article.strip().split()[:400])
    article, abstract, entityDict = get_article_summary_from_file_and_anonymize(summaryfile=firstsentencefile, articlefile=restbodyfile)
    article = " ".join(article.strip().split()[:400])
    # write entity dictionary to file
    with open(entityfile, 'w') as file:
        file.write(json.dumps(entityDict))  # use `json.loads` to do the reverse

    rb_foutput.write(article + "\n")
    fs_foutput.write(abstract + "\n")

  rb_foutput.close()
  fs_foutput.close()

  print("Finished writing file %s, %s\n" % (out_file_rb, out_file_fs))

if __name__ == '__main__':

  # Create some new directories
  if not os.path.exists(finished_files_dir): os.makedirs(finished_files_dir)

  nlp = spacy.load("en_core_web_sm")
  print("spaCy model loaded")

  # Read the tokenized stories, do a little postprocessing then write to text files
  write_to_bin_anonymized("test", os.path.join(finished_files_dir, "test.anonymized.document"), os.path.join(finished_files_dir, "test.anonymized.summary"))
  write_to_bin_anonymized("validation", os.path.join(finished_files_dir, "validation.anonymized.document"), os.path.join(finished_files_dir, "validation.anonymized.summary"))
  write_to_bin_anonymized("train", os.path.join(finished_files_dir, "train.anonymized.document"), os.path.join(finished_files_dir, "train.anonymized.summary"))
	
