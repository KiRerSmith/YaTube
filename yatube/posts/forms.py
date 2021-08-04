from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']

    def clean_text(self):
        data = self.cleaned_data['text']
        if data is None:
            raise forms.ValidationError('Напишите текст')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

    def clean_text(self):
        data = self.cleaned_data['text']
        if data is None:
            raise forms.ValidationError('Напишите текст')
        return data
