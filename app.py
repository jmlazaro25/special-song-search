import streamlit as st
from PIL import Image
from datetime import time, timedelta

import special_song_search as sss


MAX_RECOMMENDATIONS = 10

# Reused strings
ARTIST = 'artist'
RECORDING = 'recording'
ARTIST_TAGS = 'artist_tags'
RECORDING_TAGS = 'recording_tags'
ARTIST_TAGS_WEIGHT = 'artist_tags_weight'
RECORDING_TAGS_WEIGHT = 'recording_tags_weight'
RECOMMENDATIONS = 'recommendations'
RECORDING_LENGTH = 'recording_length'
RECORDING_DATE = 'recording_date'
CONDITION = 'condition'
RANGE = 'range'
CENTER = 'center'
POINTS_PER_SECOND = 'points_per_second'
POINTS_PER_YEAR = 'points_per_year'
MAX = 'max'

EXPLAIN_TEXT = """
    Motivation:
        Existing song recomendation services:
        - Use stubborn collaborative models which are slow to learn your individual preferences
        - Make repeated suggestions too often which also limits discovery potential
        - Collect personal data

    Build:
        1. Artist and recording metadata are collected from the MusicBrainz API.
        2. Data is stored database-agnostically via SQLalchemy (see schema below).
        3. Values entered on this webpage are used to query recordings from the database.
            - This includes selecting a score which is a linear sum of match values plus a random factor which will also be exposed to the user.
    """

USAGE = """
    Usage:\\
        1. Add any number of artist-related or recording-related tags you like.\\
        2. Give each tag as well as each category a weight.\\
            - They do not need to be on any particular scale but should be relative to each other for best results.\\
        3. Song (recording) length and year options are under "More."\\
        4. Submit at the bottom of the "Options" column.
    """


def main() -> None:

    st.set_page_config(
        page_title='Special Song Search',
        page_icon=Image.open('images/3s_logo_no_sub.png'),
        layout='wide',
        initial_sidebar_state='auto',
        menu_items=None
    )

    st.markdown("""
        <style>
            .block-container {padding-top: 0 !important;}
        </style>""",
        unsafe_allow_html=True,
    )

    st.title('Special Song Search')

    st.info(USAGE)

    with st.expander('About:'):
        st.text(EXPLAIN_TEXT)
        st.markdown(
        """[Github repository](https://github.com/jmlazaro25/special-song-search)""",
        unsafe_allow_html=True
        )
        st.image(Image.open('images/sss_db_white.drawio.png'))

    col_1, col_2 = st.columns((2,2))

    sql_session = init_sql_session()
    with sql_session:

        with col_1:
            st.header('Options')

            # Official Releases Filter
            st.checkbox('Officially Released Only', False, key='official_only')

            # Artist Tags
            display_tags(sql_session, ARTIST)

            # Recording Tags
            display_tags(sql_session, RECORDING)

            # Other recording params
            with st.expander('More'):
                display_recording_length()
                display_recording_date()

            # Submit
            st.button('Submit', on_click=lambda: get_recommendations(sql_session))

        with col_2:
            st.header('Recommendations')
            if RECOMMENDATIONS in st.session_state:
                display_recommendations()

    st.divider()
    st.button('Clear', on_click=clear)

    return

@st.cache_resource
def init_sql_session():
    _, sql_sessionmaker = sss.database.init_db('main')
    return sql_sessionmaker()

@st.cache_data
def get_tag_options_cached(_session, tag_type):
    return sss.recommend.get_tag_options(_session, tag_type)

def get_recommendations(_session):

    def get_tags(tag_type):
        if tag_type == ARTIST:
            tags = ARTIST_TAGS
        elif tag_type == RECORDING:
            tags = RECORDING_TAGS
        return {
            st.session_state[f'{tag_type}_tag_{tag_num}']:
            st.session_state[f'{tag_type}_weight_{tag_num}']
            for tag_num in st.session_state[tags]
        }

    def get_recording_dict(attr: str):
        if attr == 'length':
            recording_attr = RECORDING_LENGTH
        elif attr == 'date':
            recording_attr = RECORDING_DATE

        recording_attr_condition = st.session_state[f'{recording_attr}_{CONDITION}']
        ret = {
            f'{recording_attr}_{CONDITION}': recording_attr_condition,
            recording_attr_condition:
                list(st.session_state[f'{recording_attr}_{recording_attr_condition}'])
                if recording_attr_condition == RANGE else
                st.session_state[f'{recording_attr}_{recording_attr_condition}']
        }
        if attr == 'length':
            if recording_attr_condition == RANGE:
                ret[recording_attr_condition] = [
                    t.minute * 60 + t.second for t in ret[recording_attr_condition]
                ]
            elif recording_attr_condition == CENTER:
                ret[recording_attr_condition] = (
                    ret[recording_attr_condition].minute * 60
                    + ret[recording_attr_condition].second
                )
        if (
                recording_attr_condition == RANGE
                and not st.session_state[f'{MAX}_{recording_attr}']
            ):
            ret[recording_attr_condition][1] = None
        if recording_attr_condition == CENTER:
            if attr == 'length':
                ret[POINTS_PER_SECOND] = st.session_state[POINTS_PER_SECOND]
            elif attr == 'date':
                ret[POINTS_PER_YEAR] = st.session_state[POINTS_PER_YEAR]

        return ret

    st.session_state[RECOMMENDATIONS] = \
        sss.recommend.recommend(
            _session,
            artist_tags=get_tags(ARTIST),
            recording_tags=get_tags(RECORDING),
            weights = {
                key: st.session_state[f'{key}_weight'] for key in (
                ARTIST_TAGS,
                RECORDING_TAGS
                ) if f'{key}_weight' in st.session_state
            },
            recording_length=get_recording_dict('length'),
            recording_date=get_recording_dict('date'),
            randomness = 1.,
        )

def display_recommendations():
    recs = st.session_state[RECOMMENDATIONS]
    if not recs:
        st.subheader('No results :disappointed:')
        st.write('Try widening your search')

    recording_mbids = set()
    for rec in st.session_state[RECOMMENDATIONS]:
        if len(recording_mbids) == MAX_RECOMMENDATIONS:
            break
        if rec['recording']['mbid'] not in recording_mbids:
            recording_mbids.add(rec['recording']['mbid'])
        else:
            continue
        st.divider()
        st.markdown(f"##### {len(recording_mbids)}. {rec['recording']['title']}")
        st.text(f"Score: {rec['score']:.2f}")
        st.text(', '.join([artist['name'] for artist in rec['artists']]))
        st.markdown(f"""
        [MusicBrainz]({sss.musicb.RECORDING_PERM_LINK.format(rec['recording']['mbid'])})
        [ListenBrainz]({sss.musicb.LISTEN_LINK.format(rec['recording']['mbid'])})
        """)

def increase_tags(tags):
    if not st.session_state[tags]:
        st.session_state[tags] = [1]
    else:
        st.session_state[tags].append(st.session_state[tags][-1] + 1)

def display_tags(session, tag_type):

    def display_tag(tag_num, tags_str):
        tag, weight, rm = st.columns((4, 1, 0.5))
        options = get_tag_options_cached(session, tag_type)
        # Should be checking if tag_num == st.session_state[tags][0] to display
        # labels for first tag, but is unaligned, so don't display until styled
        label_vis = 'visible' if tag_num == None else 'collapsed'
        tag.selectbox(
            label='Tag',
            options=options,
            key=f'{tag_type}_tag_{tag_num}',
            placeholder='tag',
            label_visibility=label_vis
            )
        weight.number_input(
            label='Weight',
            value=0,
            key=f'{tag_type}_weight_{tag_num}',
            label_visibility=label_vis
            )
        def del_tag():
            del st.session_state[f'{tag_type}_tag_{tag_num}']
            del st.session_state[f'{tag_type}_weight_{tag_num}']
            st.session_state[tags_str].remove(tag_num)
        rm.button(':no_entry:', key=f'rm_{tag_type}_{tag_num}', on_click=del_tag)

    if tag_type == ARTIST:
        tags = ARTIST_TAGS
        weight = ARTIST_TAGS_WEIGHT
    elif tag_type == RECORDING:
        tags = RECORDING_TAGS
        weight = RECORDING_TAGS_WEIGHT

    st.subheader(f'{tag_type} tags'.title())
    st.number_input(
        label=f'{tag_type} tag weight multiplier'.title(),
        value=1,
        key=weight
    )

    if tags not in st.session_state:
        st.session_state[tags] = []

    for n in st.session_state[tags]:
        display_tag(tag_num=n, tags_str=tags)

    st.button(f'add {tag_type} tag'.title(), on_click=lambda: increase_tags(tags))
    st.divider()

def display_recording_length():
    st.subheader('Recording Length')
    recording_length_radio = st.radio(
        'Condition',
        ['range', 'center'],
        key=f'{RECORDING_LENGTH}_{CONDITION}',
    )

    if recording_length_radio == RANGE:
        st.info(''':information_source: Filters out ALL recordings outside stated range''')
        st.slider(
            'Recording Length Range:',
            time(0,0), time(0,10),
            (time(0,0), time(0,10)),
            step=timedelta(seconds=1),
            format='m:ss',
            key=f'{RECORDING_LENGTH}_{RANGE}',
        )
        st.checkbox('Enforce max recording length', value=True, key=f'{MAX}_{RECORDING_LENGTH}')
    elif recording_length_radio == CENTER:
        st.info(
            ''':information_source: Reduces recordings' scores by "Points per second"
            for each second shorter or longer than the "Center" time'''
        )
        st.slider(
            'Recording Length Center:',
            time(0,0), time(0,10),
            time(0,3,30),
            step=timedelta(seconds=1),
            format='m:ss',
            key=f'{RECORDING_LENGTH}_{CENTER}'
        )
        st.number_input(
            'Points per second',
            value=1.,
            key=POINTS_PER_SECOND
        )

def display_recording_date():
    st.subheader('Recording Year')
    recording_date_radio = st.radio(
        'Condition',
        ['range', 'center'],
        key=f'{RECORDING_DATE}_{CONDITION}',
    )

    if recording_date_radio == RANGE:
        st.info(''':information_source: Filters out ALL recordings outside stated range''')
        st.slider(
            'Recording Date Range:',
            1900, 2025,
            (1900, 2025),
            key=f'{RECORDING_DATE}_{RANGE}'
        )
        st.checkbox('Enforce max recording year', value=True, key=f'{MAX}_{RECORDING_DATE}')
    elif recording_date_radio == CENTER:
        st.info(
            ''':information_source: Reduces recordings' scores by "Points per year"
            for each year before or after "Center" year'''
        )
        st.slider(
            'Recording Year Center:',
            1900, 2025,
            2020,
            key=f'{RECORDING_DATE}_{CENTER}'
        )
        st.number_input(
            'Points per year',
            value=1.,
            key=POINTS_PER_YEAR
        )

def clear():
    for key in st.session_state:
        del st.session_state[key]


if __name__ == '__main__':
    main()
