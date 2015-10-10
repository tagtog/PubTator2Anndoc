from os import listdir
from os.path import isfile, join, dirname
from yattag import Doc
from yattag import indent
import json

class PubTator2TagTog():

    GNORMPLUS_ENTITY_CLASSES = {'Gene': 'e_1', 'FamilyName': 'e_2',
                    'DomainMotif': 'e_3', 'Species': 'e_4'}
    """
    GNormPlus uses the entity classes Gene, Family Name, Domain Motif and
    Species. They have been assigned TagTog equivalent classes e_1, e_2, e_3
    and e_4 respectively. Use your own entity class dictionary if the PubTator
    format is different.
    """

    # Update Tagger as per PubTator
    TAGGER = 'ml:GNormPlus'

    # Update Confidence as per Tagger's performance
    CONFIDENCE = 1.0

    def __init__(self, entity_classes):
        """Constructor

        Intialize the class with a dictionary of entity classes.

        Args:
            entity_classes (dict): A dictionary of entity classes
                        (key-value pairs) where the key corresponds to the
                        class in PubTator format, and the value corresponds to
                        the class in TagTog. For an example, see
                        PubTatot2TagTog.GNORMPLUS_ENTITY_CLASSES
        """
        self.entity_classes = entity_classes

    def __to_html(self, pmid, title, abstract, output_dir):
        """Generate HTML file for TagTog

        Write a HTML file required for TagTog, formatted according to TagTog's
        standards that can be viewed at the link below.
        https://github.com/jmcejuela/tagtog-doc/wiki

        By default, the MEDLINE identifier will be used as the title, unless
        something else is specified.

        Args:
            title (str): Title of the paper
            abstract (str): Abstract contents of the paper
            output_file (Optional[str]): Path to the output file. Defaults to
                                        none.

        """
        doc, tag, text = Doc().tagtext()

        # Compute hashId (TODO find out what hashing is used, currently random)
        hashId = self.__random_hashId(pmid)

        # Use Yattag to generate HTML syntax
        doc.asis('<!DOCTYPE html>')
        with tag('html',
                ('data-origid', pmid),
                ('data-anndoc-version', "2.0"),
                ('lang', ""), ('xml:lang', ""),
                ('xmlns', "http://www.w3.org/1999/xhtml"),
                klass='anndoc',
                id=hashId):
            with tag('head'):
                doc.stag('meta', charset='UTF-8')
                doc.stag('meta', name='generator', content='org.rostlab.relna')
                with tag('title'):
                    text(hashId)
            with tag('body'):
                with tag('article'):
                    with tag('section', ('data-type', 'title')):
                        with tag('h2', id='s1h1'):
                            text(title)
                    with tag('section', ('data-type', 'abstract')):
                        with tag('h3', id='s2h1'):
                            text("Abstract")
                        with tag('div', klass='content'):
                            with tag('p', id='s2p1'):
                                text(abstract)

        # Write to file
        result = indent(doc.getvalue())
        try:
            with open(join(output_dir, pmid+'.html'), 'w') as fw:
                fw.write(result)
        except IOError as e:
            print 'I/O Error({0}): {1}'.format(e.errno, e.strerror)
            raise

    def __random_hashId(self, pmid):
        """Random hash generator

        Generate a random 32-bit hash and return the hash concatenated with the
        Pubmed ID.

        Args:
            pmid (str): The Pubmed identifier of the document.

        Returns:
            str: A random hash concatenated with Pubmed ID
        """

        import uuid
        return str(uuid.uuid4().hex)+':'+pmid

    def __to_json(self, pmid, tagtog_json, output_dir):
        """Write TagTog JSON Object to file

        Write the generated TagTog JSON objecto to file. By default, the output
        file is PMID.ann.json. The JSON format for TagTog can be viewed at
        https://github.com/jmcejuela/tagtog-doc/wiki/ann.json

        Args:
            pmid (str): The Pubmed identifier of the document.
            tagtog_json (dict): A dictionary containing TagTog compatible JSON
                                object.
            output_file (Optional[str]): Path to output file. Defaults to None.
        """
        try:
            with open(join(output_dir, pmid+'.ann.json'), 'w') as fw:
                fw.write(json.dumps(tagtog_json, sort_keys=True, indent=2, separators=(',', ': ')))
        except IOError as e:
            print 'I/O Error({0}): {1}'.format(e.errno, e.strerror)
            raise

    def parse(self, input_file, output_dir=None):
        """Parse the input file

        Parse the input file. A Pubtator file can contain multiple entries.
        Each will be separated by an empty line. The program breaks a single
        file into multiple entries and processes each one separately.

        Args:
            input_file (str): Path to input file
        """
        try:
            with open(input_file) as fp:
                file_contents = fp.read()
        except IOError as e:
            print 'I/O Error({0}): {1}'.format(e.errno, e.strerror)
            raise

        # Split file_contents at an empty line.
        pubtator_entries = file_contents.split("\n\n")

        if (output_dir==None):
            output_dir = dirname(input_file)

        for entry in pubtator_entries:
            if (entry!='\n'):
                # Parse entity separately.
                self.__parse_entry(entry, output_dir)

    def __parse_entry(self, entry, output_dir):
        """Parse each separate entry

        Each line in an entry starts with the Pubmed identifier. The first line
        contains the title. The second line contains the abstract and the rest
        of the lines that follow describe the entity. Each entity is described
        by a single line of 6 tab separated values. These values are:
            1. Pubmed ID
            2. Start offset
            3. End offset
            4. Entity text
            5. Entity class
            6. Entity normalization, for example:
                - In case of Gene, it refers to the NCBI Gene Id
                - In case of Disease, it refers to the OMIM entry
                - In case of Species, it refers to the Uniprot Taxonomy ID

        Args:
            entry (str): An individual entry from the PubTator file
            output_dir (str): The output directory where the files need to be
                            written.
        """

        # Get HTML content
        lines = entry.split('\n')

        # Get PMID
        pmid = lines[0].split('|')[0]

        # Get title of the paper
        title = lines[0].split('|')[2]
        cutoff = len(title)

        # Get abstract of the paper
        abstract = lines[1].split('|')[2]

        # Write HTML
        self.__to_html(pmid, title, abstract, output_dir)

        # Generate JSON
        tagtog_json = {}
        tagtog_json['annotatable'] = {}
        tagtog_json['annotatable']['parts'] = ["s1h1", "s2h1", "s2p1"]
        tagtog_json['anncomplete'] = False
        tagtog_json['sources'] = []
        tagtog_json['sources'].append({"name": "MEDLINE", "id": pmid,
                        "url": "http://www.ncbi.nlm.nih.gov/pubmed/"+pmid})
        tagtog_json['relations']=[]
        tagtog_json['metas']={}
        tagtog_json['entities']=[]

        for i in range(2, len(lines)):

            #Define empty entity dictionary
            entity = {}
            line = lines[i].split('\t')

            # Start offset
            startOffset = int(line[1])
            part = 's1h1'
            if startOffset > cutoff:
                startOffset -= cutoff
                part = 's2p1'

            # Entity text
            text = line[3]

            # Set entity properties
            if (line[0]==pmid):
                entity["part"] = part
                entity["offsets"] = [{"start": startOffset, "text": text}]
            entity["confidence"] = {"prob": PubTator2TagTog.CONFIDENCE,
                        "state": "", "who": [PubTator2TagTog.TAGGER]}
            entity['classId'] = self.entity_classes[line[4]]

            #TODO get normalization definition from TagTog
            entity["normalizations"] = {}

            # Append each entity to TagTog JSON Object
            tagtog_json['entities'].append(entity)

        # Write JSON to file
        self.__to_json(pmid, tagtog_json, output_dir)

def main():
    pub2tag = PubTator2TagTog(PubTator2TagTog.GNORMPLUS_ENTITY_CLASSES)
    pub2tag.parse('/home/ashish/mthesis-ashish/miscellaneous/RESTfulAPI.client/Python/result.txt')

if __name__=='__main__':
    main()