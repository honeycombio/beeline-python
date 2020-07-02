from __future__ import absolute_import
import unittest
from mock import Mock, patch

import jinja2
import beeline.patch.jinja2
assert beeline.patch.jinja2  # make pyflake stop complainings


class TestJinja2Patch(unittest.TestCase):
    def test_wrapper_executes(self):

        with patch('beeline.patch.jinja2.beeline') as m_beeline:
            m_span = Mock()
            m_beeline.start_span.return_value = m_span

            t = jinja2.Template("my template")
            t.render()
            m_beeline.start_span.assert_called_once_with(context={
                "name": "jinja2_render_template",
                "template.name": "[string]",
            })
            m_beeline.finish_span.assert_called_once_with(m_span)

            m_beeline.reset_mock()
            m_beeline.start_span.return_value = m_span

            t = jinja2.Template("my template")
            t.name = 'foo'
            t.render()
            m_beeline.start_span.assert_called_once_with(context={
                "name": "jinja2_render_template",
                "template.name": "foo",
            })
            m_beeline.finish_span.assert_called_once_with(m_span)
