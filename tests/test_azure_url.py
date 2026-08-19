from expert_choice.backends.openai_compat import azure_v1_base_url


def test_default_openai_azure_v1_url():
    assert (
        azure_v1_base_url("https://myres.openai.azure.com")
        == "https://myres.openai.azure.com/openai/v1/"
    )


def test_rewrites_services_host_to_openai_azure():
    assert (
        azure_v1_base_url("https://myres.services.ai.azure.com")
        == "https://myres.openai.azure.com/openai/v1/"
    )


def test_keeps_foundry_project_path():
    assert (
        azure_v1_base_url(
            "https://myres.services.ai.azure.com/api/projects/proj"
        )
        == "https://myres.services.ai.azure.com/api/projects/proj/openai/v1/"
    )
