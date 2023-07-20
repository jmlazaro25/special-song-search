import streamlit as st
from dotenv import load_dotenv
from os import environ

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
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title('Special Song Search')

    col_1, col_2 = st.columns((3,2))

    with col_1:
        st.header('Options')

        st.subheader('Artist Tags')
        if 'artist_tags' not in st.session_state:
            st.session_state['artist_tags'] = 0

        for n in range(st.session_state['artist_tags']):
            display_tag(n)

        st.button('Add Atrist Tag', on_click=increase_artist_tags)

    with col_2:
        st.header('Recommendations')

    return

@st.cache_resource
def init_sql_session():
    _, sql_sessionmaker = sss.database.connect()
    return sql_sessionmaker()

def increase_artist_tags():
    st.session_state['artist_tags'] += 1

def display_tag(index):
    tag, weight = st.columns((4, 1))
    tag.selectbox('Tag', ['hip hop', 'pop'], key=f'tag_{index}')
    weight.number_input('Weight', key=f'weight_{index}')

if __name__ == '__main__':
    main()
