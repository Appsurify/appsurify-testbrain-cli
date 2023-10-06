import re


RE_OCTAL_BYTE = re.compile("\\\\([0-9]{3})")


RE_COMMIT_DIFF = re.compile(
        r"""
^diff[ ]--git
    [ ](?P<a_path_fallback>"?[ab]/.+?"?)[ ](?P<b_path_fallback>"?[ab]/.+?"?)\n
(?:^old[ ]mode[ ](?P<old_mode>\d+)\n
   ^new[ ]mode[ ](?P<new_mode>\d+)(?:\n|$))?
(?:^similarity[ ]index[ ]\d+%\n
   ^rename[ ]from[ ](?P<rename_from>.*)\n
   ^rename[ ]to[ ](?P<rename_to>.*)(?:\n|$))?
(?:^new[ ]file[ ]mode[ ](?P<new_file_mode>.+)(?:\n|$))?
(?:^deleted[ ]file[ ]mode[ ](?P<deleted_file_mode>.+)(?:\n|$))?
(?:^similarity[ ]index[ ]\d+%\n
   ^copy[ ]from[ ].*\n
   ^copy[ ]to[ ](?P<copied_file_name>.*)(?:\n|$))?
(?:^index[ ](?P<a_blob_id>[0-9A-Fa-f]+)
    \.\.(?P<b_blob_id>[0-9A-Fa-f]+)[ ]?(?P<b_mode>.+)?(?:\n|$))?
(?:^---[ ](?P<a_path>[^\t\n\r\f\v]*)[\t\r\f\v]*(?:\n|$))?
(?:^\+\+\+[ ](?P<b_path>[^\t\n\r\f\v]*)[\t\r\f\v]*(?:\n|$))?
                            """,
        re.VERBOSE | re.MULTILINE,
    )


RE_COMMIT_LIST = re.compile(
        ("COMMIT:\t(?P<sha>[0-9A-Fa-f]+)\n"
         "TREE:\t(?P<tree>[0-9A-Fa-f]+)\n"
         "DATE:\t(?P<date>.*)\n"
         "AUTHOR:\t(?P<author>.+\t.+\t.*)\n"
         "COMMITTER:\t(?P<committer>.+\t.+\t.*)\n"
         "MESSAGE:\t(?P<message>.*)\n"
         "PARENTS:\t(?P<parents>.*)(\n{0,2})?"
         "(?P<stats>(?:\d\t\d\t.+\n)+)?(\n{1,2})?"
         "(?P<patch>(?:diff[ ]--git(?:.+\n?)+)+)?"),
        re.MULTILINE)


RE_REPO_NAME_PATTERN = re.compile(".*\/([^\/]+)\/?")