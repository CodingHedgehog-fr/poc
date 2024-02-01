import requests
import httpx
import json
import asyncio
from datetime import datetime
from itertools import chain

POKEMON_BASE_URL = f'https://pokeapi.co/api/v2/pokemon'
POKE_PER_PAGE = 10
POKE_DETAILS_TIMEOUT = 30


# ---------------------------------------------------------------------------------------------------------------------
# Asynchronous version
# ---------------------------------------------------------------------------------------------------------------------
async def get_pokemon_names_async(client: httpx.AsyncClient, max_pokemons: int = None) -> list:
    """Gets pokémon's names from a public consumption-only API (Asynchronous process)
       Note: request is split into sub requests, each sub request is a coroutine that gets ONE page of pokémon.
       All Sub requests are executed CONCURRENTLY
    Args:
        client: an AsyncClient representing the HTTP client session
        max_pokemons (optional): an int representing the maximum number of pokémon to retrieve
    Returns:
        a list containing names
    Raises:
        None
    """

    response = await client.get(POKEMON_BASE_URL)
    if response.status_code != 200:
        print('Api did not respond with status code 200!')
        return []

    json_obj = json.loads(response.content)

    nb_poke = json_obj['count'] if max_pokemons is None else max_pokemons
    coroutines = []
    offset = 0
    while offset < nb_poke:
        coroutines.append(get_pokemon_page_async(client, f'{POKEMON_BASE_URL}/?offset={offset}&limit={POKE_PER_PAGE}'))
        offset += POKE_PER_PAGE

    names_per_page = await asyncio.gather(*coroutines)
    return list(chain.from_iterable(names_per_page))


async def get_pokemon_page_async(client: httpx.AsyncClient, url: str) -> list:
    """Gets pokémon's names from a specific page (Asynchronous process)
    Args:
        client: an AsyncClient representing the HTTP client session
        url: a string representing a specific pokémon url page
    Returns:
        a list containing all names of the page
    Raises:
        None
    """

    print(f"retrieving url: {url}")
    response = await client.get(url, timeout=10)
    if response.status_code != 200:
        print('Api did not respond with status code 200!')
        return []

    json_obj = json.loads(response.content)
    return [poke['name'] for poke in json_obj['results']]


async def get_pokemon_details_async(client: httpx.AsyncClient, url: str) -> dict:
    """Gets pokémon's details from the pokémon's specific url (Asynchronous process)
    Args:
        client: an AsyncClient representing the HTTP client session
        url: a string representing an url
    Returns:
        a dictionary containing all pokémon's properties
    Raises:
        None
    """

    print(f"retrieving details from url: {url}")
    response = await client.get(url, timeout=POKE_DETAILS_TIMEOUT)
    if response.status_code != 200:
        print('Api did not respond with status code 200!')
        return {}

    return json.loads(response.content)


async def get_pokemons_async(number: int = 100) -> dict:
    """Builds a dictionary of pokémon (Asynchronous process)
    Args:
        number (optional): an int representing the number of pokémon to retrieve
    Returns:
        a dictionary containing all pokémon along with their properties
    Raises:
        None
    """

    pokemons = {}
    async with httpx.AsyncClient() as client:
        coroutines = [get_pokemon_details_async(client, f'{POKEMON_BASE_URL}/{name}')
                      for name in await get_pokemon_names_async(client, max_pokemons=number)]

        for poke_detail in await asyncio.gather(*coroutines):
            pokemons[poke_detail['name']] = poke_detail
            print(f"Pokemon '{poke_detail['name']}' saved in dictionary...")

    return pokemons


# ---------------------------------------------------------------------------------------------------------------------
# Synchronous version
# ---------------------------------------------------------------------------------------------------------------------
def get_pokemon_names_sync(max_pokemons: int = None) -> list:
    """Gets pokémon' names from a public consumption-only API (Synchronous process)
       Note: request is split into sub requests, each sub request is a function that gets ONE page of pokémons.
       All Sub requests are executed SEQUENTIALLY
    Args:
        max_pokemons (optional): an int representing the maximum number of pokémons to retrieve
    Returns:
        a list containing names
    Raises:
        None
    """

    response = requests.get(POKEMON_BASE_URL)
    if response.status_code != 200:
        print('Api did not respond with status code 200!')
        return []

    json_obj = json.loads(response.content)

    nb_poke = json_obj['count'] if max_pokemons is None else max_pokemons
    names = []
    offset = 0
    while offset < nb_poke:
        names.extend(get_pokemon_page_sync(f'{POKEMON_BASE_URL}/?offset={offset}&limit={POKE_PER_PAGE}'))
        offset += POKE_PER_PAGE

    return names


def get_pokemon_details_sync(url: str) -> dict:
    """Gets pokémon's details from the pokémon's specific url (Synchronous process)
    Args:
        url: a string representing an url
    Returns:
        a dictionary containing all pokémon's properties
    Raises:
        None
    """

    print(f"retrieving details from url: {url}")
    response = requests.get(url, timeout=POKE_DETAILS_TIMEOUT)
    if response.status_code != 200:
        print('Api did not respond with status code 200!')
        return {}

    return json.loads(response.content)


def get_pokemon_page_sync(url: str) -> list:
    """Gets pokémon's names from a specific page (Synchronous process)
    Args:
        url: a string representing a specific pokémon url page
    Returns:
        a list containing all names of the page
    Raises:
        None
    """

    print(f"retrieving url: {url}")
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        print('Api did not respond with status code 200!')
        return []

    json_obj = json.loads(response.content)
    return [poke['name'] for poke in json_obj['results']]


def get_pokemons_sync(number: int = 100) -> dict:
    """Builds a dictionary of pokémon (Synchronous process)
    Args:
        number (optional): an int representing the number of pokémon to retrieve
    Returns:
        a dictionary containing all pokémon along with their properties
    Raises:
        None
    """

    pokemons = {}
    for name in get_pokemon_names_sync(max_pokemons=number):
        poke_detail = get_pokemon_details_sync(f'{POKEMON_BASE_URL}/{name}')
        pokemons[poke_detail['name']] = poke_detail
        print(f"Pokemon '{poke_detail['name']}' saved in dictionary...")

    return pokemons


def compare_sync_async():
    """This proof of concept compares 2 ways of retrieving data from a public consumption-only API :
       Asynchronous process (asyncio & HTTPX) vs synchronous process (requests)
    Args:
    Returns:
        None
    Raises:
        None
    """

    # run asynchronous version
    max_pokemons = 1302
    start = datetime.now()
    pokemons_async = asyncio.run(get_pokemons_async(number=max_pokemons))
    elapsed_async = datetime.now() - start
    print(f"Asynchronous process ran in {elapsed_async}s")

    # run synchronous version
    start = datetime.now()
    pokemons_sync = get_pokemons_sync(number=max_pokemons)
    elapsed_sync = datetime.now() - start
    print(f"synchronous process ran in {elapsed_sync}s")

    # compare results
    print(f"number of pokemons with async process: {len(pokemons_async)}")
    print(f"number of pokemons with sync process: {len(pokemons_sync)}")
    print(f"Asynchronous process is {elapsed_sync / elapsed_async:.1f} faster than synchronous process!!")


if __name__ == '__main__':
    compare_sync_async()
