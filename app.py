import streamlit as st

import special_song_search as sss


def main() -> None:

    st.set_page_config(
        page_title='Special Song Search',
        page_icon=':ice:',
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

    col_1, col_2 = st.columns((2,2))

    sql_session = init_sql_session()
    with sql_session:

        with col_1:
            st.header('Options')

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
            res = st.button(
                'Submit',
                on_click=lambda: get_recommendations(sql_session, st.session_state)
            )
            print(res)

        with col_2:
            st.header('Recommendations')
            if 'recommendations' in st.session_state:
                display_recommendations()

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
    rm.button('🗑️', key=f'{tag_type}_rm_{index}', on_click=None)

@st.cache_data
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
        st.write(
            f"""Title: {rec['recording']['title']}
            Score: {rec['score']}"""
            )
        st.write('\t'+', '.join([artist['name'] for artist in rec['artists']]))

def clear():
    for key in st.session_state:
        del st.session_state[key]


if __name__ == '__main__':
    main()
