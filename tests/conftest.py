from pytest_djangoapp import configure_djangoapp_plugin


pytest_plugins = configure_djangoapp_plugin(
    {
         'LANGUAGE_CODE': 'ru',
    },
    admin_contrib=True,
)
