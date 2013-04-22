from glob import glob


def parse_log(file, lines_max=100, re_head=None):
    files = {}
    for log in glob(file + '*'):
        if log == file:
            files[-1] = log
        else:
            ext = log.rsplit('.', 1)[-1]
            files[int(ext)] = log

    lines = []
    lines_ = []
    for i, log in sorted(files.items()):
        with open(log) as fd:
            for line in reversed(fd.read().splitlines()):
                lines_.insert(0, line)
                if not re_head or re_head.search(line):
                    lines.extend(lines_)
                    lines_ = []

        if len(lines) >= lines_max:
            break

    return lines[:lines_max]
