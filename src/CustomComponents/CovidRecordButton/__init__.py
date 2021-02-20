import os
import time
import streamlit as st
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
# (This is, of course, optional - there are innumerable ways to manage your
# release process.)
_RELEASE = True

# Declare a Streamlit component. `declare_component` returns a function
# that is used to create instances of the component. We're naming this
# function "_component_func", with an underscore prefix, because we don't want
# to expose it directly to users. Instead, we will create a custom wrapper
# function, below, that will serve as our component's public API.

# It's worth noting that this call to `declare_component` is the
# *only thing* you need to do to create the binding between Streamlit and
# your component frontend. Everything else we do in this file is simply a
# best practice.

if not _RELEASE:
    _component_func = components.declare_component(
        "covid-record-button",
        # Pass `url` here to tell Streamlit that the component will be served
        # by the local dev server that you run via `npm run start`.
        # (This is useful while your component is in development.)
        url="http://localhost:3001",
    )
else:
    # When we're distributing a production version of the component, we'll
    # replace the `url` param with `path`, and point it to to the component's
    # build directory:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("covid-record-button", path=build_dir)


# Create a wrapper function for the component. This is an optional
# best practice - we could simply expose the component function returned by
# `declare_component` and call it done. The wrapper allows us to customize
# our component's API: we can pre-process its input args, post-process its
# output value, and add a docstring for users.
def CovidRecordButton(duration=5000.0, key=None):
    """Create a new instance of "CovidRecordButton".

    Parameters
    ----------
    goal_duration: int or float
        The number of miliseconds the component should record for. Will only
        be approximated.
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.

    Returns
    -------
    recording
        A 5 second cough recording stored as a WAV byte array.
        (This is the value passed to `Streamlit.setComponentValue` on the
        frontend.)

    """
    # Call through to our private component function. Arguments we pass here
    # will be sent to the frontend, where they'll be available in an "args"
    # dictionary.
    #
    # "default" is a special argument that specifies the initial return
    # value of the component before the user has interacted with it.
    approx_duration = duration + 600
    recording = _component_func(duration=approx_duration, key=key, default=None)

    # Check if button was clicked, otherwise, recording is delivered
    if recording == 'clicked':
        status = st.empty()
        progress = st.empty()

        # Display progress bar
        second_duration = duration / 1000
        status.warning(f'Recording... 0.0/{second_duration:.1f}s')
        for percent_complete in range(100):
            time.sleep(second_duration / 100)
            status.warning(f'Recording... {(percent_complete / 100 * second_duration):.1f}/{second_duration:.1f}s')
            progress.progress(percent_complete + 1)

        status.empty()
        progress.empty()
        return None

    # We could modify the value returned from the component if we wanted.
    # There's no need to do this in our simple example - but it's an option.
    return recording

# Add some test code to play with the component while it's in development.
# During development, we can run this just as we would any other Streamlit
# app: `$ streamlit run my_component/__init__.py`
if not _RELEASE:
    import streamlit as st

    st.subheader("Covid Recording Button")

    # Create an instance of our component with a constant `name` arg, and
    # print its output value.
    recording_data = CovidRecordButton(duration=5000)
    if recording_data:
        st.write(recording_data['url'])

    st.markdown("---")
