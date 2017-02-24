if __name__ == '__main__':
    from github import Github

    # First create a Github instance:
    g = Github()

    oec = g.get_repo('OpenExoplanetCatalogue/open_exoplanet_catalogue')

    pulls = oec.get_pulls()

    for pull in pulls:
        print(pull)
