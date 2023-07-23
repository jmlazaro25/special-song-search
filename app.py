import streamlit as st
from PIL import Image

import special_song_search as sss


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

    with st.expander("How Special Song Search works:"):
        st.text("""
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

        Usage:
            1. Add any number of artist-related or recording-related tags you like.
            2. Give each tag as well as each category a weight.
                - They do not need to be on any particular scale but should be relative to each other for best results.
            3. Submit at the bottom of the "Options" column.
            4. Stay tuned for more options like recording length and number of recommendations.
        """)
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

            # Artist Tags
            st.subheader('Artist Tags')
            st.number_input(
                label='Total Artist Tags Weight',
                key='artist_tags_weight'
            )
            if 'artist_tags' not in st.session_state:
                st.session_state['artist_tags'] = 0

            for n in range(st.session_state['artist_tags']):
                display_tag(sql_session, 'artist', n)

            st.button('Add Atrist Tag', on_click=increase_artist_tags)
            st.divider()

            # Recording Tags
            st.subheader('Recording Tags')
            st.number_input(
                label='Total Recording Tags Weight',
                key='recording_tags_weight'
            )
            if 'recording_tags' not in st.session_state:
                st.session_state['recording_tags'] = 0

            for n in range(st.session_state['recording_tags']):
                display_tag(sql_session, 'recording', n)

            st.button('Add Recording Tag', on_click=increase_recording_tags)
            st.divider()

            # Other recording params

            # Submit
            st.button(
                'Submit',
                on_click=lambda: get_recommendations(sql_session, st.session_state)
            )

        with col_2:
            st.header('Recommendations')
            if 'recommendations' in st.session_state:
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

def increase_artist_tags():
    st.session_state['artist_tags'] += 1

def increase_recording_tags():
    st.session_state['recording_tags'] += 1

def display_tag(session, tag_type, index):
    tag, weight, rm = st.columns((4, 1, 0.5))
    options = get_tag_options_cached(session, tag_type)
    label_vis = 'visible' if index == 0 else 'collapsed'
    tag.selectbox(
        label='Tag',
        options=options,
        key=f'{tag_type}_tag_{index}',
        placeholder='tag',
        label_visibility=label_vis
        )
    weight.number_input(
        label='Weight',
        key=f'{tag_type}_weight_{index}',
        label_visibility=label_vis
        )
    rm.button(':no_entry:', key=f'{tag_type}_rm_{index}', on_click=None)

#@st.cache_data
def get_recommendations(_session, _session_state):
    st.session_state['recommendations'] = \
        sss.recommend.recommend(
            _session,
            artist_tags = {
                key: weight for key, weight in st.session_state.items()
                if key.startswith('artist_tag')
            },
            recording_tags = {
                key: weight for key, weight in st.session_state.items()
                if key.startswith('recording_tag')
            },
            recording_length = tuple(),
            weights = {
                key: st.session_state[f'{key}_weight'] for key in (
                'artist_tags',
                'recording_tags'
                ) if f'{key}_weight' in st.session_state
                },
            randomness = 1.,
            limit = 10
        )

def display_recommendations():
    for rec in st.session_state['recommendations']:
        st.divider()
        st.markdown(f"##### {rec['recording']['title']}")
        st.text(f"Score: {rec['score']}")
        st.text(', '.join([artist['name'] for artist in rec['artists']]))
        st.markdown(f"""
        [MusicBrainz]({sss.musicb.RECORDING_PERM_LINK.format(rec['recording']['mbid'])})
        [ListenBrainz]({sss.musicb.LISTEN_LINK.format(rec['recording']['mbid'])})
        """)

def clear():
    for key in st.session_state:
        del st.session_state[key]


if __name__ == '__main__':
    main()
