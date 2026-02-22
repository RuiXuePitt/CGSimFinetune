IGNORE_INDEX = -100

def _find_all_subseq(haystack, needle):
    """return list of start indices where needle occurs in haystack"""
    if not needle:
        return []
    out = []
    n = len(needle)
    for i in range(len(haystack) - n + 1):
        if haystack[i:i+n] == needle:
            out.append(i)
    return out

def build_labels_by_special_tags(input_ids, tokenizer):
    """
    Unmask tokens inside each assistant block:
      <|start_header_id|>assistant<|end_header_id|> ... <|eot_id|>
    Mask everything else, incl. TOOL_RESPONSE blocks.
    """
    labels = [IGNORE_INDEX] * len(input_ids)

    # these must be actual special tokens in tokenizer
    a_start = tokenizer.encode("<|start_header_id|>assistant<|end_header_id|>", add_special_tokens=False)
    eot     = tokenizer.encode("<|eot_id|>", add_special_tokens=False)

    # optional: mask TOOL_RESPONSE blocks even if they appear inside (usually they don't)
    tr_start = tokenizer.encode("<TOOL_RESPONSE>", add_special_tokens=False)
    tr_end   = tokenizer.encode("</TOOL_RESPONSE>", add_special_tokens=False)

    # find assistant block starts
    a_starts = _find_all_subseq(input_ids, a_start)

    for s in a_starts:
        # content begins right after the assistant header tokens
        content_start = s + len(a_start)

        # find the next eot after content_start
        eots = [i for i in _find_all_subseq(input_ids[content_start:], eot)]
        if not eots:
            continue
        eot_pos = content_start + eots[0]  # index where <|eot_id|> begins

        # AFTER: include the eot tokens
        eot_end = min(eot_pos + len(eot), len(input_ids))
        for i in range(content_start, eot_end):
            labels[i] = input_ids[i]

    # mask TOOL_RESPONSE blocks (safety, in your template they are in user blocks anyway)
    trs = _find_all_subseq(input_ids, tr_start)
    for s in trs:
        ends = _find_all_subseq(input_ids[s+len(tr_start):], tr_end)
        if not ends:
            continue
        e = s + len(tr_start) + ends[0] + len(tr_end)
        for i in range(s, e):
            labels[i] = IGNORE_INDEX

    return labels

def tokenize_and_mask(example, tokenizer, max_length=5120):
    text = tokenizer.apply_chat_template(
        example["messages"],
        tools=example.get("tools"),
        tokenize=False,
        add_generation_prompt=False,
    )
    enc = tokenizer(text, truncation=True, max_length=max_length, add_special_tokens=False)
    input_ids = enc["input_ids"]
    labels = build_labels_by_special_tags(input_ids, tokenizer)
    return {"input_ids": input_ids, "attention_mask": enc["attention_mask"], "labels": labels}