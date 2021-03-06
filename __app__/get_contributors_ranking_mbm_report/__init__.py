"""Copyright since 2020, EPAM Systems

   This file is part of OSCI.

   OSCI is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   OSCI is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with OSCI.  If not, see <http://www.gnu.org/licenses/>."""

import datetime
import json
import logging
import traceback as tb

import azure.functions as func

from __app__.config import Config
from __app__.datalake.reports.company.contributors import ContributorsRankingMTD
from __app__.datalake.reports.company.month_by_month_contributors import ContributorsRankingMBM
from __app__.datalake.schemas.public import ContributorsRankingReportSchema
from __app__.get_contributors_ranking_mbm_report.process import get_contributors_ranking_mbm_change_report
from __app__.utils import get_req_param

DAY_FORMAT = "%Y-%m-%d"
DEFAULT_DAY = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(DAY_FORMAT)
log = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s', level=logging.DEBUG)
    try:
        log.info(f"Http trigger. req.params: {req.params}")
        date = datetime.datetime.strptime(get_req_param(req, 'date', default=DEFAULT_DAY), DAY_FORMAT)
        company = get_req_param(req, 'company', default=Config().default_company)
        contributors_report = ContributorsRankingMTD(date=date, company=company)
        contributors_mbm_report = ContributorsRankingMBM(date=date, company=company)

        df = get_contributors_ranking_mbm_change_report(
            reports=contributors_report.read_all(),
            contributor_field=ContributorsRankingReportSchema.author,
            commits_amount_field=ContributorsRankingReportSchema.commits
        )
        contributors_mbm_report.save(df=df)
        return func.HttpResponse(json.dumps(dict(out_df=str(df))))
    except Exception as ex:
        log.error(f'Exception {ex}')
        log.exception(ex)
        return func.HttpResponse(f"This HTTP triggered function failed {ex} "
                                 f"{''.join(tb.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))}",
                                 status_code=500)
