import csv
import os
from subprocess import call
from typing import Iterable

from settings import BASE_DIR


majestic_million_path = os.path.join(BASE_DIR, 'vendor/majestic_million.csv')
if not os.path.isfile(majestic_million_path):
    call(['vendor/update'])


class MajesticMillionSite:
    def __init__(
            self, rank: int, tld_rank: int, domain: str, tld: str, subnets: str,
            ips: str, idn_domain: str, idn_tld: str, prev_rank: int,
            prev_tld_rank: int, prev_subnets: str, prev_ips: str):
        self.rank = rank
        self.tld_rank = tld_rank
        self.domain = domain
        self.tld = tld
        self.subnets = subnets
        self.ips = ips
        self.idn_domain = idn_domain
        self.idn_tld = idn_tld
        self.prev_rank = prev_rank
        self.prev_tld_rank = prev_tld_rank
        self.prev_subnets = prev_subnets
        self.prev_ips = prev_ips

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))

    def __str__(self) -> str:
        return '{}: {}'.format(self.rank, self.domain)


def get_sites(rank: int, count: int) -> Iterable[MajesticMillionSite]:
    start = rank  # first line is headline, therefore index begins at 1
    end = start + count - 1
    if start not in range(1, 1000001) or end not in range(1, 1000001):
        raise ValueError(
            'valid indexes are 1 to 1 million. (requested: %s-%s)' % (start, end))

    result = []
    with open(majestic_million_path) as csvfile:
        reader = csv.reader(csvfile)

        # skip headline
        next(reader)

        for (rank, tld_rank, domain, tld, subnets, ips, idn_domain, idn_tld,
             prev_rank, prev_tld_rank, prev_subnets, prev_ips) in reader:
            rank = int(rank)
            tld_rank = int(tld_rank)
            prev_rank = int(prev_rank)
            prev_tld_rank = int(prev_tld_rank)
            if rank < start:
                continue
            if rank > end:
                break
            yield MajesticMillionSite(
                rank=rank,
                tld_rank=tld_rank,
                domain=domain,
                tld=tld,
                subnets=subnets,
                ips=ips,
                idn_domain=idn_domain,
                idn_tld=idn_tld,
                prev_rank=prev_rank,
                prev_tld_rank=prev_tld_rank,
                prev_subnets=prev_subnets,
                prev_ips=prev_ips)


    return result
