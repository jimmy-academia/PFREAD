from typing import List, Dict, Any
import re

# Helper function to find the end of a balanced brace group.
def find_braced_content_end(text: str, start_index: int) -> int:
    """
    Given text and a starting index of '{', finds the index of the matching '}'.
    Returns -1 if not found.
    """
    if text[start_index] != '{':
        return -1
    
    depth = 1
    i = start_index + 1
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    
    return i if depth == 0 else -1

def preprocess_and_replace_floats(latex: str) -> tuple[str, Dict[str, str]]:
    """
    Replaces float environments (figure, table) with unique placeholders
    and returns the modified text alongside a dictionary of the replacements.
    """
    replacements = {}
    counter = 0
    env_pattern = re.compile(r'\\begin\{(figure|table|figure\*|table\*)\}(.*?)\\end\{\1\}', re.DOTALL)

    def replacer(match):
        nonlocal counter
        env_name = match.group(1).replace('*', '')
        content = match.group(2)

        # Find the caption command and its full content robustly
        full_caption_command = None
        caption_match = re.search(r'\\caption\s*{', content)
        if caption_match:
            end_idx = find_braced_content_end(content, caption_match.end() - 1)
            if end_idx != -1:
                full_caption_command = content[caption_match.start():end_idx].strip()

        # Find the label
        label_match = re.search(r'\\label\{(.*?)\}', content)
        
        if label_match and full_caption_command:
            label_content = label_match.group(1).strip()
            
            # This is the desired final output for the float
            replacement_text = f"({env_name}: {label_content})\n{full_caption_command}"
            
            # Create a unique placeholder
            key = f"__FLOAT_PLACEHOLDER_{counter}__"
            replacements[key] = replacement_text
            counter += 1
            
            # Return the key, ensuring it's treated as a separate paragraph
            return f"\n\n{key}\n\n"
        
        # If no caption or label is found, remove the environment entirely
        return ""

    processed_latex = env_pattern.sub(replacer, latex)
    return processed_latex, replacements

def extract_and_remove_abstract(latex: str) -> tuple[str | None, str]:
    """
    Finds the abstract environment, extracts its content, and returns the
    content along with the latex string with the abstract environment removed.
    """
    pattern = re.compile(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', re.DOTALL)
    match = pattern.search(latex)
    
    if match:
        abstract_content = match.group(1).strip()
        # Remove the abstract from the main text to avoid double processing
        latex_without_abstract = pattern.sub('', latex)
        return abstract_content, latex_without_abstract
    else:
        # Return None for content if no abstract is found
        return None, latex

def extract_blocks(text: str, command: str) -> List[Dict[str, str]]:
    pattern = rf'\\{command}\{{(.*?)\}}'
    matches = list(re.finditer(pattern, text, re.DOTALL))
    blocks = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append({
            'title': match.group(1).strip(),
            'content': text[start:end].strip()
        })
    return blocks

def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r'\n\s*\n+', text) if p.strip()]

def extract_footnotes(text: str) -> List[tuple]:
    results = []
    pattern = re.compile(r'\\footnote\{')
    i = 0
    while i < len(text):
        m = pattern.search(text, i)
        if not m:
            break
        start = m.start()
        end_brace = find_braced_content_end(text, m.end() - 1)
        if end_brace != -1:
            results.append((start, end_brace))
            i = end_brace
        else: # Unbalanced brace, skip to avoid infinite loop
            i = m.end()
    return results

def split_sentences(paragraph: str) -> List[str]:
    footnotes = extract_footnotes(paragraph)
    segments = []
    last_idx = 0

    for start, end in footnotes:
        before = paragraph[last_idx:start].strip()
        if before:
            segments.extend(re.split(r'(?<=[.!?])\s+', before))
        segments.append(paragraph[start:end].strip())
        last_idx = end

    after = paragraph[last_idx:].strip()
    if after:
        segments.extend(re.split(r'(?<=[.!?])\s+', after))

    return [s.strip() for s in segments if s.strip()]

def process_text_block(text: str) -> List[List[str]]:
    return [split_sentences(p) for p in split_paragraphs(text)]

def split_latex_structure(latex: str) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
    # Pre-process the LaTeX to handle floats, returning cleaned text and a replacement map
    latex, float_replacements = preprocess_and_replace_floats(latex)
    
    # Extract and remove the abstract from the main text
    abstract_content, latex = extract_and_remove_abstract(latex)

    structured = []
    
    # Process and add the abstract to the structured list if it was found
    if abstract_content:
        abstract_dict = {
            'section': 'Abstract',
            'paragraphs': process_text_block(abstract_content)
        }
        structured.append(abstract_dict)

    # Continue processing the rest of the document for sections
    for section in extract_blocks(latex, 'section'):
        section_dict = {'section': section['title'], 'subsections': []}
        subsections = extract_blocks(section['content'], 'subsection')

        if not subsections:
            section_dict['paragraphs'] = process_text_block(section['content'])
        else:
            for sub in subsections:
                subsection_dict = {'subsection': sub['title'], 'subsubsections': []}
                subsubsections = extract_blocks(sub['content'], 'subsubsection')

                if not subsubsections:
                    subsection_dict['paragraphs'] = process_text_block(sub['content'])
                else:
                    for subsub in subsubsections:
                        subsub_dict = {'subsubsection': subsub['title'], 'paragraphs': []}
                        paragraphs = extract_blocks(subsub['content'], 'paragraph')

                        if not paragraphs:
                            subsub_dict['paragraphs'] = process_text_block(subsub['content'])
                        else:
                            subsub_dict['paragraphs'] = []
                            for para in paragraphs:
                                sentences = split_sentences(para['content'])
                                subsub_dict['paragraphs'].append(sentences)
                        
                        subsection_dict['subsubsections'].append(subsub_dict)
                
                section_dict['subsections'].append(subsection_dict)

        structured.append(section_dict)

    return structured, float_replacements

def show_sentences_interactively(structured: List[Dict[str, Any]], replacements: Dict[str, str]):
    """
    Displays sentences, substituting placeholders with their actual content.
    """
    for sec in structured:
        tag = "Section: {sec['section']}" if sec['section'] != 'Abstract' else "Abstract"
        print(f"\n=== {tag} ===")
        subsections = sec.get('subsections', [])
        if not subsections:
            for para in sec.get('paragraphs', []):
                for sentence in para:
                    # Look up the sentence in the replacements dict; default to sentence itself
                    output = replacements.get(sentence, sentence)
                    print(output)
                    input()
            continue

        for sub in subsections:
            print(f"\n  -- Subsection: {sub['subsection']}")
            subsubs = sub.get('subsubsections', [])
            if not subsubs:
                for para in sub.get('paragraphs', []):
                    for sentence in para:
                        output = replacements.get(sentence, sentence)
                        print(output)
                        input()
                continue

            for subsub in subsubs:
                print(f"\n    --- Subsubsection: {subsub['subsubsection']}")
                for para in subsub.get('paragraphs', []):
                    for sentence in para:
                        output = replacements.get(sentence, sentence)
                        print(output)
                        input()


# --- EXAMPLE USAGE ---
if __name__ == '__main__':
    latex_example = r"""
\begin{abstract}
This is the first sentence of the abstract. This is the second.
And a third sentence concludes the abstract.
\end{abstract}

\section{Introduction}
This is the first sentence of the introduction. Here is a second sentence.
This is a sentence with a footnote\footnote{This is a footnote. It has a period.}.

Here is another paragraph. It stands on its own.

\begin{figure*}
  \centering
  \includegraphics[width=\linewidth]{imgs/problem-tiny.jpg}
  \vspace{-6mm}
  \caption{Illustration of the NP$^3$R full (NP$^3$R) problem.}
  \vspace{-4mm}
  \label{fig:problem-illustration}
\end{figure*}

This paragraph comes after the figure. Let's see how it's handled.

\subsection{Background}
This is the first sentence of a subsection.

"""

    # 1. Parse the LaTeX structure
    structured_data, float_map = split_latex_structure(latex_example)
    
    # 2. Display the content interactively
    show_sentences_interactively(structured_data, float_map)