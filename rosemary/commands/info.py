import click
import base64
import pkg_resources


def get_metadata_value(metadata_lines, key):
    default_value = f"{key}: Unknown"
    line = next((line for line in metadata_lines if line.startswith(key)), default_value)
    return line.split(':', 1)[1].strip() if line != default_value else default_value.split(':', 1)[1].strip()


@click.command()
def info():
    """Displays information about the Rosemary CLI."""
    distribution = pkg_resources.get_distribution("rosemary")

    try:
        metadata = distribution.get_metadata_lines('METADATA')
        author = get_metadata_value(metadata, 'Author')
        author_email = get_metadata_value(metadata, 'Author-email')
        description = get_metadata_value(metadata, 'Summary')
    except FileNotFoundError:
        author, author_email, description = "Unknown", "Unknown", "Not available"

    name = distribution.project_name
    version = distribution.version

    click.echo(f"Name: {name}")
    click.echo(f"Version: {version}")
    click.echo(f"Author: {author}")
    click.echo(f"Author-email: {author_email}")
    click.echo(f"Description: {description}")


@click.command('love:me', hidden=True)
@click.option('--again', is_flag=True)
def info2(again):
    if not again:
        click.echo(click.style("Love me --again?", fg='magenta'))
        return

    lyrics = "ICAgIA0KICAgIEtub3cgSSd2ZSBkb25lIHdyb25nLA0KICAgIExlZnQgeW91ciBoZWFydCB0b3JuDQogICAgSXMgdGhhdCB3aGF0IGRldmlscyBkbz8NCiAgICBUb29rIHlvdSBzbyBsb3csDQogICAgV2hlcmUgb25seSBmb29scyBnbw0KICAgIEkgc2hvb2sgdGhlIGFuZ2VsIGluIHlvdSENCiAgICANCiAgICBOb3cgSSdtIHJpc2luZyBmcm9tIHRoZSBncm91bmQNCiAgICBSaXNpbmcgdXAgdG8geW91IQ0KICAgIEZpbGxlZCB3aXRoIGFsbCB0aGUgc3RyZW5ndGggSSd2ZSBmb3VuZCwNCiAgICBUaGVyZSdzIG5vdGhpbmcgSSBjYW4ndCBkbyENCiAgICANCiAgICBJIG5lZWQgdG8ga25vdyBub3csIGtub3cgbm93LCBjYW4geW91IGxvdmUgbWUgYWdhaW4/DQogICAgSSBuZWVkIHRvIGtub3cgbm93LCBrbm93IG5vdywgY2FuIHlvdSBsb3ZlIG1lIGFnYWluPw0KICAgIEkgbmVlZCB0byBrbm93IG5vdywga25vdyBub3csIGNhbiB5b3UgbG92ZSBtZSBhZ2Fpbj8NCiAgICBJIG5lZWQgdG8ga25vdyBub3csIGtub3cgbm93LCBjYW4geW91IGxvdmUgbWUgYWdhaW4/DQogICAgDQogICAgSSdsbCBzcGluIHlvdSBhcm91bmQsIHdvbid0IGxldCB5b3UgZmFsbCBkb3duLA0KICAgIFdvdWxkIHlvdSBsZXQgbWUgZG93bj8gTm8hDQogICAgSSdsbCBzcGluIHlvdSBhcm91bmQsIHdvbid0IGxldCB5b3UgZmFsbCBkb3duLA0KICAgIFdvdWxkIHlvdSBsZXQgbWUgZG93bj8gTm8hDQogICAgDQogICAgTm93IEknbSByaXNpbmcgZnJvbSB0aGUgZ3JvdW5kDQogICAgUmlzaW5nIHVwIHRvIHlvdSENCiAgICBGaWxsZWQgd2l0aCBhbGwgdGhlIHN0cmVuZ3RoIEkndmUgZm91bmQsDQogICAgVGhlcmUncyBub3RoaW5nIEkgY2FuJ3QgZG8hDQogICAgDQogICAgSSBuZWVkIHRvIGtub3cgbm93LCBrbm93IG5vdywgY2FuIHlvdSBsb3ZlIG1lIGFnYWluPw0KICAgIEkgbmVlZCB0byBrbm93IG5vdywga25vdyBub3csIGNhbiB5b3UgbG92ZSBtZSBhZ2Fpbj8NCiAgICBJIG5lZWQgdG8ga25vdyBub3csIGtub3cgbm93LCBjYW4geW91IGxvdmUgbWUgYWdhaW4/DQogICAgSSBuZWVkIHRvIGtub3cgbm93LCBrbm93IG5vdywgY2FuIHlvdSBsb3ZlIG1lIGFnYWluPw0KDQogICAgQ29uZ3JhdHVsYXRpb25zLCB5b3UgZm91bmQgdGhlIGVhc3RlciBlZ2ch" # noqa

    decoded = decode_lyrics(lyrics)
    colored_lyrics = colorize_lyrics(decoded)
    click.echo(colored_lyrics)


def colorize_lyrics(lyrics):
    colored_lyrics = ""
    colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']

    for i, line in enumerate(lyrics.splitlines()):
        colored_lyrics += click.style(line, fg=colors[i % len(colors)]) + '\n'

    return colored_lyrics


def decode_lyrics(encoded_lyrics):
    decoded_lyrics = base64.b64decode(encoded_lyrics.encode('utf-8')).decode('utf-8')
    return decoded_lyrics
