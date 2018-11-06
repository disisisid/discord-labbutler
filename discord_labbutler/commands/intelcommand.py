import logging
import requests
from requests.exceptions import RequestException
import json
from discord import Embed
from discord_labbutler.command import Command, CommandException, CommandMessage
from urllib.parse import quote
from difflib import SequenceMatcher


class IntelCommand(Command):
    """**Fetches information about an Intel processor and displays it.**`"""

    def run(self, ctx, args):
        # No query given
        if args is None:
            raise CommandException('You\'ve got to enter a search string.')

        processor = self._ark_search(args)

        message = Embed(
            title=processor['ProductName'],
            color=0x0071c5,  # Easteregg: The original intel blue!
            url=processor['Link']
        )

        # Thumbnail icon
        message.set_thumbnail(url=processor['BrandBadge'])

        # Details
        message.add_field(name='Cores/Threads',
                          value='{}/{}'.format(
                              processor['CoreCount'],
                              processor['ThreadCount']))
        message.add_field(name='Clock speed',
                          value='{} to {}'.format(
                              processor['ClockSpeed'],
                              processor['ClockSpeedMax']))
        message.add_field(name='Cache',
                          value=processor['Cache'])
        message.add_field(name='Release date',
                          value=processor['BornOnDate'])
        message.add_field(name='Maximum memory',
                          value=processor['MaxMem'])
        message.add_field(name='Supported memory',
                          value=processor['MemoryTypes'])
        message.add_field(name='ECC memory support',
                          value=('yes' if processor['ECCMemory'] else 'no'))
        message.add_field(name='Scalability',
                          value=processor['ScalableSockets'])
        message.add_field(name='Socket',
                          value=processor['SocketsSupported'].strip())
        message.add_field(name='Litography',
                          value=processor['Lithography'].strip())

        # Done!
        return CommandMessage(embed=message)

    def _ark_search(self, query):
        """Fetch results from odata.intel.com."""

        try:
            uri = ''.join([
                "https://odata.intel.com",
                "/API/v1_0/Products/Processors()",
                "?$filter=substringof('{}', ProductName) eq true",
                "&$format=json",
                "&$orderby=ProductName",
                "&$top=10"
            ]).format(quote(query))
            results = json.loads(requests.get(uri, verify=False).text)["d"]

            if len(results) < 1:
                raise CommandException('There is no processor with that name.')

            best_result = 0.0
            result = None

            for entry in results:
                confidence = SequenceMatcher(None, query,
                                             entry['ProcessorNumber']).ratio()

                if confidence > best_result:
                    best_result = confidence
                    result = entry

            return result

        except Exception as e:
            # Some kind of network/http error
            logging.warn("Cannot fetch intel ark data: {}".format(e))
            raise CommandException(
                'The Intel bot does\'t like talking to me :(')
