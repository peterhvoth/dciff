from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo

wp = Client('http://dciff-indie.org/xmlrpc.php', 'deirdreep@yahoo.com', 'dcif@ir2012')
wp.call(GetPosts())

wp.call(GetUserInfo())

post = WordPressPost()
post.title = 'My new title'
post.content = 'This is the body of my new post.'
post.terms_names = {
  'post_tag': ['test', 'firstpost'],
  'category': ['Introductions', 'Tests']
}
wp.call(NewPost(post))